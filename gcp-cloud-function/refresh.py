import git
from pathlib import Path
import tempfile
from google.cloud import storage

MOHREPO_URL = "https://github.com/MoH-Malaysia/covid19-public"
CITFREPO_URL = "https://github.com/CITF-Malaysia/citf-public"

def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    print("Starting execution")
    mohdirobj = tempfile.TemporaryDirectory()
    mohdir_fp = Path(mohdirobj.name)
    citfdirobj = tempfile.TemporaryDirectory()
    citfdir_fp = Path(citfdirobj.name)

    client = storage.Client()
    bucket = client.lookup_bucket("msia-covid-api-data-bucket")
    print("Set up storage client and bucket")

    # Retrieve MOH repo
    try:
        mohrepo = git.Repo.clone_from(MOHREPO_URL, mohdir_fp, depth=1)
        latest_mohrepo_commit_datetime = mohrepo.commit().committed_datetime

    except git.GitCommandError as e:
        print("Failed to clone MOH repo! Thrown exception:")
        print(e)

    print("Cloned MOH repo")

    # Retrieve CITF repo
    try:
        citfrepo = git.Repo.clone_from(CITFREPO_URL, citfdir_fp, depth=1)
        latest_citfrepo_commit_datetime = citfrepo.commit().committed_datetime

    except git.GitCommandError as e:
        print("Failed to clone CITF repo! Thrown exception:")
        print(e)

    print("Cloned CITF repo")

    epidemic_files = [
        "cases_malaysia.csv", "cases_state.csv", "deaths_malaysia.csv", "deaths_state.csv", "icu.csv", "hospital.csv", "pkrc.csv", "tests_malaysia.csv", "tests_state.csv"
    ]
    vax_files = ["vax_malaysia.csv", "vax_state.csv"]

    # Upload files in epidemic/
    for i in epidemic_files:
        blob = bucket.blob(i)
        blob.upload_from_filename(mohdir_fp / "epidemic" / i)

    # Upload files in vax/
    for i in vax_files:
        blob = bucket.blob(i)
        blob.upload_from_filename(citfdir_fp / "vaccination" / i)

    print("Done cloning and uploading files to bucket!")
