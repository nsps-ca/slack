This repository provides code to have a bot for the NSPS in our Slack workspace.

## events.py

This checks the NSPS calendar and sees if there's an event on the given day. If it is, it posts a message to the `#chat` channel in Slack. A message will appear in
Slack as the `Grip` user. The token for this Slack user is stored in secrets.
