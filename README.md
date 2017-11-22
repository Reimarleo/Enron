# Enron

## Dataset downlod address:
https://www.kaggle.com/wcukierski/enron-email-dataset

## Dataset description
The dataset consists of message strings sitting in a single column, and containing
information about senders, recipients, timestamps, subjects and the content of the
messages themselves.

## Part 1 of the process
The dataset is parsed and the following filed are created into a pandas dataframe.

- (a) Date sent
- (b) Time sent
- (c) Sender
- (d) Recipients
- (e) Subject
- (f) Content

The data is then written out as a JSON file.

## Part 2 of the process

Additional information is added to the dataset to allow extraction of ordered email conversations.

- (a) datetime filed to sort the dataframe chronologically
- (b) Sorted list of participants (senter + recipients) in each email
- (c) Unique ID of conversation, based on the combination of sorted list of participants and subject

This is not a perfect method as it doesn't account for email addresses being added or removed from a conversation. 
It is also not abvious what constitutes a conversation.

## Running the script

The script require the input data file to be named emails.csv and to be located in the same directory where the py file is located. Also the outputs will be written in the same direcory. The outputs are:

1. A JSON file with the processed data
2. A conversation extracted from the data and written in chronological orl order

## Language and libraries
Python 3.6

- os
- re
- datetime
- pandas

