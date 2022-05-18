from __future__ import annotations
import os
import random
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yaml

EMAIL_USERNAME = os.environ.get("EMAIL_USERNAME")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")


@dataclass
class Elf:
    name: str
    email: str
    secrets: List[str] = None
    significant: Optional[Elf] = None

    def __repr__(self):
        return f"Elf(name={self.name}, secrets={', '.join([e.name for e in self.secrets])})"


def load_elves() -> List[Elf]:
    with open("elves.yml") as elf_file:
        doc = yaml.load(elf_file.read(), Loader=yaml.FullLoader)

    elves = {}
    for elf in doc:
        elves[elf] = Elf(
            name=elf, email=doc[elf].get("email"), secrets=[], significant=None
        )

    # Assign signficant others
    for elf in doc:
        if doc[elf].get("significant"):
            elves[elf].significant = elves[doc[elf].get("significant")]

    return elves


# No elf may have themselves
# No elf may have their significant other
# No elf may have the same target twice
def draw_round(elves: Dict[str, Elf]) -> Dict[str, Elf]:
    # Algorithm: Quantum
    while True:
        elf_names = list(elves)
        random.shuffle(elf_names)

        # Check rules
        for elf, secret in zip(elves, elf_names):
            if elves[elf].name == secret:
                break

            if elves[elf].significant and elves[elf].significant.name == secret:
                break

            if secret in [e.name for e in elves[elf].secrets]:
                break
        else:
            # Passed checks
            for elf, secret in zip(elves, elf_names):
                elves[elf].secrets.append(elves[secret])

            return elves


def get_email_server(username: str, password: str) -> smtplib.SMTP_SSL:
    # Create a secure SSL context
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=context)
    server.login(username, password)
    return server


def send_emails(elves: Dict[str, Elf]) -> None:
    emails = []
    for elf in elves:
        subject = f"{elf.name}'s Secret Santa Report"
        secrets = "\n".join([e.name for e in elf.secrets])
        body = f"Hi {elf.name},\n\nYou have been assigned:\n{secrets}\n\nThank you for your hard work,\nSanta"

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_USERNAME
        message["To"] = elf.email
        body = body.replace("\n", "<br>")
        mime_body = MIMEText("<html><body>" + body + "</body></html>", "html")
        message.attach(mime_body)
        emails.append([receiver, message])

    with get_email_server(EMAIL_USERNAME, EMAIL_PASSWORD) as server:
        for receiver, message in emails:
            server.sendmail(EMAIL_USERNAME, [receiver], message.as_string())


elves = load_elves()
elves = draw_round(elves)
elves = draw_round(elves)
send_emails(elves)
