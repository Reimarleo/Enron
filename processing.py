import os
import re
import datetime
import pandas as pd

# Performs the main data transformation process
def transform_data(df):
    for i, row in df.iterrows():
        is_field_content = False
        is_field_date = False
        is_field_from = False
        is_field_to = False
        is_field_subject = False
        content_string = ''
        lines = row['message'].splitlines()
        line_index = 0
        for line in lines:
            line_index += 1
            if 'X-FileName:' in line:
                is_field_content = True
                continue # Skip the actual X-FileName field
            
            if not is_field_content:
                if ':' in line:
                    field, value = line.split(":", 1)
                    field = field.strip()
                    value = value.strip()
                    
                    # Establish the field being processed at the current line
                    is_field_date = True if (field == 'Date' and line_index == 2) else False
                    is_field_from = True if (field == 'From' and line_index == 3) else False
                    
                    if field == 'To':
                        is_field_to = True
                    if field == 'Subject':
                        is_field_to = False
                        is_field_subject = True
                    if field == 'Mime-Version':
                        is_field_subject = False
                    
                    # Write values
                    if is_field_date:
                        date = re.findall(r'\d{1,2} \w{3} \d{4}', value)[0]
                        time = re.findall(r'\d{2}:\d{2}:\d{2}', value)[0]
                        df = df.set_value(i, 'Date', date)                    
                        df = df.set_value(i, 'Time', time)
                    if is_field_from:
                        df = df.set_value(i, 'Sender', value)
                    if is_field_to:
                        is_field_to = True
                        df = df.set_value(i, 'Recipients', value)
                    if field == 'Subject' and is_field_subject:
                        df = df.set_value(i, 'Subject', value)
                    elif field != 'Subject' and is_field_subject:
                        df = df.set_value(i, 'Subject', df.iloc[i]['Subject'] + "\n" + field + ': ' + value)
    
                # This deals with email addresses and subjects on multiple lines
                else:
                    if is_field_to:
                        df = df.set_value(i, 'Recipients', df.iloc[i]['Recipients'] + " " + line.strip())
                    if is_field_subject:
                        df = df.set_value(i, 'Subject', df.iloc[i]['Subject'] + "\n" + line.strip())
            # Build content string
            else:
                content_string += line + "\n"
                
        # Replace tabs with spaces to avoid problems when the file is opend in Excel
        content_string.replace('\t', ' ')
        # Write content string to df once built
        df = df.set_value(i, 'Content', content_string)
        
    # Original columns are no longer required
    df.drop('file', axis=1, inplace=True)
    df.drop('message', axis=1, inplace=True)   
    return df

# adds date and time in the datetime format to allow sorting by time
def add_datetime(df):    
    for i, row in df.iterrows():
        date_time_string = row['Date'] + " " + row['Time']
        datetime_object = datetime.datetime.strptime(date_time_string, '%d %b %Y %H:%M:%S')
        df = df.set_value(i, 'datetime', datetime_object)  
    return df

# Creates a sorted list of email addresses in the conversation
def create_list_participants(df):
    df['Participants'] = ''
    df['Participants'] = df['Participants'].astype(object)
    for i, row in df.iterrows():
        set_emails = set()
        list_emails_recipients = row['Recipients'].split(',')
        for email in list_emails_recipients:
            set_emails.add(email.strip())
        set_emails.add(row['Sender'])
        set_emails = sorted(set_emails)
        df = df.set_value(i, 'Participants', set_emails)    
    return df

# Removes Re: so the first and subsequent emails can be matched
def remove_re(text):
    if text[:4] == 'RE: ' or text[:4] == 'Re: ':
        text = text[4:]
    if text[:3] == 'RE:' or text[:3] == 'Re:':
        text = text[3:]
    return text

# Using subject and list of participants create a unique ID for each conversation
def create_unique_conv_id(df):
    dict_comb_id = dict()
    id_n = 0
    # Remove RE: from subject to find first email as well
    df['Subject'] = df['Subject'].map(remove_re)

    for i, row in df.iterrows():
        combination = str(row['Participants']) + " - " + row['Subject']
        if combination in dict_comb_id:
            conversation_id = dict_comb_id[combination]
            df = df.set_value(i, 'conversation_id', conversation_id)
        else:
            id_n += 1
            dict_comb_id[combination] = id_n
            df = df.set_value(i, 'conversation_id', id_n)
    return df


# Function to take a conversation ID as input and outputs a txt file with the full conversation
def write_out_conversation(df, conversation_id):
    output_string = ''
    output_path = os.path.join(working_folder, 'Conversation' + str(conversation_id) + '.txt')
    # Create a dataframe with only the emails from the conversation, already sorted
    sub_df = df[df['conversation_id'] == conversation_id]
    for i, row in sub_df.iterrows():
        output_string += 'To: ' + row['Recipients'] + '\n'
        output_string += 'From: ' + row['Sender'] + '\n'
        output_string += 'Time: ' + str(row['datetime']) + '\n\n'
        output_string += row['Content'] + '\n\n'
        output_string += '--------------------------' + '\n\n'
    # Write file as text
    with open(output_path, 'w') as out:
        out.write(output_string)    
    return


# Process
if __name__ == "__main__":
    # Define paths
    working_folder = os.path.dirname(__file__)
    path_input = os.path.join(working_folder, 'emails.csv')
    path_output = os.path.join(working_folder, 'output.json')
    
    # Load data to pandas dataframe
    df = pd.read_csv(path_input, encoding = 'utf8');
    
    # Add required fields and drop original data
    df = transform_data(df)
    
    # Remove duplicate records
    # NOTE: some dups are not removed due to new line characters in one of the instances
    # This would have to be dealt with, having more time
    df.drop_duplicates(subset=None, keep='first', inplace=True)
    
    # Fix errors in date
    df['Date'] = df['Date'].str.replace('0001','2001')
    df['Date'] = df['Date'].str.replace('0002','2002')
    
    # Write out df in json format
    df.to_json(path_output, orient='records', lines=True)
    
    # Add datetime object to df
    df = add_datetime(df)
    
    # Replace nans with the string 'empty'. Not all emails have a visible recipient
    df['Recipients'].fillna('empty', inplace=True)
    
    # Create list of people in the conversation
    df = create_list_participants(df)
    
    # Create unique conversation ID
    df = create_unique_conv_id(df)
    
    # Sort df based on conversations and date
    df = df.sort_values(['conversation_id', 'datetime'], ascending=[True, True])

    # Add the lenght of the conversation by counting instances of the ID
    df['conversation_lenght'] = df.groupby(['conversation_id'])['conversation_id'].transform('count')
    
    # Write a random conversation
    conv_id_to_print = 189111
    write_out_conversation(df, conv_id_to_print)
    
    
    
