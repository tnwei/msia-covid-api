import argparse
import difflib
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shelve

import git
import pandas as pd
from tqdm import tqdm


def return_moh_schema(filepath: Path) -> Tuple[Dict, Dict]:
    schema = {}
    errors = {}
    for i in filepath.glob("epidemic/**/*.csv"):
        try:
            df = pd.read_csv(i)
            schema[i.name] = list(df.columns)
        except pd.errors.ParserError as e:
            # Cater for key-in errors breaking the schema
            one_file_error = []
            one_file_error.append("Data entry error, cannot read directly as CSV")
            print(f"Error reading file {i} with following exception:")
            print(e)

            with open(i, "r") as f:
                # Read the header
                cols = f.readline().strip()
            cols = [i.strip() for i in cols.split(",")]
            print("Columns parsed directly from file instead:")
            print(cols)

            schema[i.name] = cols
            errors[i.name] = one_file_error

    for i in filepath.glob("mysejahtera/**/*.csv"):
        try:
            df = pd.read_csv(i)
            schema[i.name] = list(df.columns)
        except pd.errors.ParserError as e:
            # Cater for key-in errors breaking the schema
            one_file_error = []
            one_file_error.append("Data entry error, cannot read directly as CSV")

            print(f"Error reading file {i} with following exception:")
            print(e)
            with open(i, "r") as f:
                # Read the header
                cols = f.readline().strip()
            cols = [i.strip() for i in cols.split(",")]
            print("Columns parsed directly from file instead:")
            print(cols)

            schema[i.name] = cols
            errors[i.name] = one_file_error

    return schema, errors


def return_citf_schema(filepath: Path) -> Tuple[Dict, Dict]:
    schema = {}
    errors = {}
    for i in filepath.glob("vaccination/**/*.csv"):
        df = pd.read_csv(i)
        schema[i.name] = list(df.columns)

    for i in filepath.glob("registration/**/*.csv"):
        df = pd.read_csv(i)
        schema[i.name] = list(df.columns)

    return schema, errors


def schema2text(schema: Dict) -> List:
    lines = []
    for i, j in schema.items():
        for col in j:
            lines.append(f"{i}: {col}\n")

    lines.sort()

    return lines


def strf_diff_output(diffoutput: List) -> List:
    if len(diffoutput) == 0:
        return []
    else:
        # Skip first two lines in diff
        pretty_output = [i for i in diffoutput[2:]]

        # Skip diff comments
        pretty_output = [i for i in pretty_output if not i.startswith("@")]

    return pretty_output


def main(repo: str, outfile: Optional[str]):
    """
    Output list of changes in data schema from MOH and CITF repo.
    Iterates over all commits in history and finds change in data columns.

    Usage
    -----
    `python generate-data-schema-changelog.py moh` or
    `python generate-data-schema-changelog.py citf`

    Args
    ----
    repo: `moh` or `citf` repo
    outputfp: output filepath, defaults to <repo>-schema-changes.txt

    Return
    ------
    None
    """
    assert repo in ["moh", "citf"], f"{repo} needs to be 'moh' or 'citf'"
    if outfile is None:
        outfile = repo + "-schema-changes.txt"

    if repo == "moh":
        repo_url = "https://github.com/MoH-Malaysia/covid19-public"
        cache_fname = ".moh-schema-cache"
        return_schema = return_moh_schema
    elif repo == "citf":
        repo_url = "https://github.com/CITF-Malaysia/citf-public"
        cache_fname = ".citf-schema-cache"
        return_schema = return_citf_schema

    # Setup data schema
    dirobj = tempfile.TemporaryDirectory()
    dirfp = Path(dirobj.name)

    # Clone
    repo_obj = git.Repo.clone_from(repo_url, dirfp)

    # Retrieve between two commits
    # commits = [i for i in repo_obj.iter_commits("b70cdc..HEAD")]

    # Retrieve all commits
    commits = [i for i in repo_obj.iter_commits(all=True)]
    commits.reverse()  # Because commits are listed last first

    # Open cache
    cache = shelve.open(cache_fname)

    print(f"Num commits total: {len(commits)}")
    num_schema_changes = 0

    # Setup header block
    title = f"Data schema changes in {repo.upper()} repo"
    underline = "=" * len(title)
    body = (
        "Format is <+ or -><filename>: <columnname>. \n"
        + "'+' means added column, '-' means removed column.\n"
        + f"Data source: {repo_url}\n"
        + "Generated with: https://github.com/tnwei/msia-covid-api/blob/master/generate-data-schema-changelog.py\n"
    )
    header_block = title + "\n" + underline + "\n" + body + "\n\n"

    writelines = []

    # Loop across the commits
    for i in tqdm(range(len(commits) - 1)):
        if commits[i].hexsha in cache.keys():
            prev_repo_schema, prev_errors = cache.get(commits[i].hexsha)
        else:
            repo_obj.git.checkout(commits[i])

            try:
                prev_repo_schema, prev_errors = return_schema(dirfp)
                cache[commits[i].hexsha] = prev_repo_schema, prev_errors
            except Exception as e:
                print(f"Errored out on commit {commits[i]} with following exception:")
                print(e)
                raise e

        if commits[i + 1].hexsha in cache.keys():
            new_repo_schema, new_errors = cache.get(commits[i + 1].hexsha)
        else:
            repo_obj.git.checkout(commits[i + 1])
            try:
                new_repo_schema, new_errors = return_schema(dirfp)
                cache[commits[i + 1].hexsha] = new_repo_schema, new_errors
            except Exception as e:
                print(f"Errored out on commit {commits[i+1]} with following exception:")
                print(e)
                raise e

        diffs = strf_diff_output(
            list(
                difflib.unified_diff(
                    schema2text(prev_repo_schema),
                    schema2text(new_repo_schema),
                    n=0,  # remove all context lines
                )
            )
        )

        errors = strf_diff_output(
            list(
                difflib.unified_diff(
                    schema2text(prev_errors),
                    schema2text(new_errors),
                    n=0,  # remove all context lines
                )
            )
        )

        if len(diffs) == 0:
            pass
        else:
            num_schema_changes += 1
            negatives = [i for i in diffs if i.startswith("-")]
            positives = [i for i in diffs if i.startswith("+")]

            title_str = f"Changes in commit {commits[i+1].hexsha[:6]} on ({commits[i+1].committed_datetime})"
            writelines.append(title_str + "\n")
            writelines.append("-" * len(title_str) + "\n")

            if len(positives) != 0:
                writelines.append("".join(positives) + "\n")
            if len(negatives) != 0:
                writelines.append("".join(negatives) + "\n")

        if len(errors) == 0:
            pass
        else:
            negatives = [i for i in errors if i.startswith("-")]
            positives = [i for i in errors if i.startswith("+")]

            negatives = [i.replace("-", "fixed: ") for i in negatives]
            positives = [i.replace("+", "error: ") for i in positives]

            title_str = f"Data errors in commit {commits[i+1].hexsha[:6]} on ({commits[i+1].committed_datetime})"
            writelines.append(title_str + "\n")
            writelines.append("-" * len(title_str) + "\n")
            if len(positives) != 0:
                writelines.append("".join(positives) + "\n")
            if len(negatives) != 0:
                writelines.append("".join(negatives) + "\n")

    cache.close()

    with open(outfile, "w") as f:
        f.write(header_block)
        f.writelines(writelines)

    print(f"{num_schema_changes} schema changes found, written to {outfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Output list of changes in data schema from MOH and CITF repo.
    Iterates over all commits in history and finds change in data columns."""
    )
    parser.add_argument(
        "repo",
        type=str,
        help="Repo to check all schema changes to date, `moh` or `citf`",
    )
    parser.add_argument(
        "--outfile",
        type=str,
        help="Output file name, defaults to <repo>-schema-changes.txt",
    )
    args = parser.parse_args()

    main(args.repo, args.outfile)
