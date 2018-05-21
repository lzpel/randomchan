#!/bin/sh
gcloud app deploy --project markov-204821 --version 1
gcloud app deploy cron.yaml --project markov-204821 --version 1
gcloud app deploy index.yaml --project markov-204821 --version 1