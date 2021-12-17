#!/usr/bin/env python3
import argparse

import environ
import requests

env = environ.Env()
environ.Env.read_env("config/settings/.env")
YOUTRACK_TOKEN = env("YOUTRACK_TOKEN")
PROJECT_SHORT_NAME = "FS"
SPECIAL_CASE_TYPE = "Enhancement"


def _get_field_value(fields, field_name):
    for field in fields:
        if field["name"] == field_name:
            return field["value"]["name"]


def _get_issues():
    url = "https://humecol.myjetbrains.com/youtrack/api/issues/"
    fields = "numberInProject,summary,customFields(name,value(name))"
    query1 = ("(project: frusale_main) "
              "and (Area: Development ) "
              "and (State: {In progress}) "
              "and (Type: -Architecting, -Exploration)")
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer {}".format(YOUTRACK_TOKEN),
        "Cache-Control": "no-cache"
    }

    response1 = requests.get(
        url,
        headers=headers,
        params={
            "fields": fields,
            "query": query1
        }
    )
    response1.raise_for_status()

    issues_in_progress = response1.json()
    issues_in_progress_ids = []
    for issue in issues_in_progress:
        issue_id = issue["numberInProject"]
        issues_in_progress_ids.append(
            "{}-{}".format(PROJECT_SHORT_NAME, issue_id)
        )

    query2 = (
        "(Subtask of: {}) "
        "and (State: Storage, Open) "
        "and (Type: -Architecting, -Exploration)"
    ).format(",".join(issues_in_progress_ids))

    response2 = requests.get(
        url,
        headers=headers,
        params={
            "fields": fields,
            "query": query2
        }
    )
    response2.raise_for_status()

    other_issues = response2.json()
    res = []
    for issue in (issues_in_progress + other_issues):
        res.append((
            "{}-{} [{}]".format(
                PROJECT_SHORT_NAME,
                issue["numberInProject"],
                _get_field_value(issue["customFields"], "Type")
            ),
            issue["summary"]
        ))

    return res


def _prepare_commit_message(file_path):
    with open(file_path, "r+") as f:
        previous_content_lines = f.readlines()
        f.seek(0, 0)
        f.write("\n\n# [{}]\n".format(SPECIAL_CASE_TYPE))
        for issue in _get_issues():
            f.write("# {} {}\n".format(issue[0], issue[1]))

        for i in range(1, len(previous_content_lines)):
            f.write(previous_content_lines[i])


def _check_commit_message_is_appropriate(file_path):
    with open(file_path, "r") as f:
        content = f.readlines()
        if len(content) > 2:
            descr_line = content[2]

            if descr_line.startswith("[{}]".format(SPECIAL_CASE_TYPE)):
                return 0

            for issue in _get_issues():
                if descr_line.startswith(issue[0]):
                    return 0
        else:
            print("There isn't appropriate start in this commit message!")
            return 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("commit_msg_file_path")
    parser.add_argument("--action",
                        default="check",
                        choices=["prepare", "check"])
    args = parser.parse_args()
    if args.action == "prepare":
        _prepare_commit_message(args.commit_msg_file_path)
    elif args.action == "check":
        return _check_commit_message_is_appropriate(args.commit_msg_file_path)


if __name__ == "__main__":
    exit(main())
