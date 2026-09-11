import os
from datetime import date

from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models import Application

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = ["Role", "Company", "Date Applied", "Salary", "Email", "Emailed", "Response", "Follow-up"]


def _credentials() -> service_account.Credentials:
    key_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if not key_file:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_SERVICE_ACCOUNT_FILE is not set. Add it to your .env file.",
        )
    if not os.path.exists(key_file):
        raise HTTPException(
            status_code=500,
            detail=f"Google service account file not found at '{key_file}'.",
        )
    return service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)


def _row_values(app: Application) -> list[str]:
    return [
        app.role,
        app.company,
        app.date_applied.isoformat() if isinstance(app.date_applied, date) else "",
        f"${app.salary:,}" if app.salary is not None else "",
        app.email,
        "Yes" if app.emailed else "No",
        "Yes" if app.response else "No",
        app.followup.isoformat() if isinstance(app.followup, date) else "",
    ]


def export_applications_to_doc(applications: list[Application]) -> dict:
    """
    Create a Google Doc with a table of all applications, share it with
    GOOGLE_USER_EMAIL, and return its id and URL.
    """
    creds = _credentials()
    docs = build("docs", "v1", credentials=creds, cache_discovery=False)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    title = f"Job Applications Export — {date.today().isoformat()}"
    rows = [HEADERS] + [_row_values(a) for a in applications]
    n_rows, n_cols = len(rows), len(HEADERS)

    try:
        doc = docs.documents().create(body={"title": title}).execute()
        document_id = doc["documentId"]

        docs.documents().batchUpdate(
            documentId=document_id,
            body={
                "requests": [
                    {
                        "insertTable": {
                            "rows": n_rows,
                            "columns": n_cols,
                            "location": {"index": 1},
                        }
                    }
                ]
            },
        ).execute()

        structure = docs.documents().get(documentId=document_id).execute()
        table = next(el["table"] for el in structure["body"]["content"] if "table" in el)
        cell_starts = [
            [cell["content"][0]["startIndex"] for cell in row["tableCells"]]
            for row in table["tableRows"]
        ]

        # Fill cells from the last one to the first so earlier indices stay valid
        # as each insertText shifts everything after it.
        fill_requests = []
        for r in range(n_rows - 1, -1, -1):
            for c in range(n_cols - 1, -1, -1):
                text = rows[r][c]
                if text:
                    fill_requests.append(
                        {
                            "insertText": {
                                "location": {"index": cell_starts[r][c]},
                                "text": str(text),
                            }
                        }
                    )

        header_bold_requests = [
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": cell_starts[0][c],
                        "endIndex": cell_starts[0][c] + len(str(rows[0][c])),
                    },
                    "textStyle": {"bold": True},
                    "fields": "bold",
                }
            }
            for c in range(n_cols)
        ]

        docs.documents().batchUpdate(
            documentId=document_id, body={"requests": fill_requests + header_bold_requests}
        ).execute()

        user_email = os.getenv("GOOGLE_USER_EMAIL")
        if user_email:
            drive.permissions().create(
                fileId=document_id,
                body={"type": "user", "role": "writer", "emailAddress": user_email},
                fields="id",
                sendNotificationEmail=False,
            ).execute()
    except HttpError as exc:
        raise HTTPException(status_code=502, detail=f"Google API error: {exc}") from exc

    return {
        "document_id": document_id,
        "url": f"https://docs.google.com/document/d/{document_id}/edit",
    }
