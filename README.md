This repository provides code to have a bot for the NSPS in our Slack workspace.

## events.py

This checks the NSPS calendar and sees if there's an event on the given day. If it is, it posts a message to the `#chat` channel in Slack. 

A message will appear in Slack as the `Grip` user. The token for this Slack user is stored in secrets.

## recordings.py

This checks the NSPS Zoom account and sees if a new recording has appeared. The recordings that have been seen are stored in `.seen-recordings`. If a new recording is seen, a Slack message will be sent to `#it-strategy`. 

A message will appear in Slack as the `Grip` user. The token for this Slack user is stored in secrets.

This also requires `ZOOM_CLIENT_ID`, `ZOOM_ACCOUNT_ID` and `ZOOM_CLIENT_SECRET` which are also stored in GitHub secrets.

App settings for `Grip` in Slack are here: https://app.slack.com/app-settings/T0ABMM43WPL/A0BCE1CDBNG/general