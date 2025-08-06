import tkinter as tk
from tkinter import scrolledtext
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os
import sys
import pathlib


# ==== Gmail API Scope ====
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# ==== ML Spam Classifier Setup ====

def get_user_path():
    return os.path.join(pathlib.Path.home(),".user_spam.pkl")
    

def load_user_spam():
    path = get_user_path()
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return []

def save_user_spam(spam_list):
    path = get_user_path()
    with open(path, "wb") as f:
        pickle.dump(spam_list, f)

user_spam = load_user_spam()
Emails = [
    "bafake5232@decodewp.com", "brightsky39@emailondeck.com", "vortex.mirror@fakeinbox.com",
    "nightowl921@moakt.cc", "zenpanda456@guerrillamail.com", "coolcloud888@10minutemail.com",
    "flashyduck01@trashmail.com", "lunarwave21@temp-mail.org", "greenowl77@dropmail.me",
    "fastfox932@maildrop.cc", "davishunterboy@gmail.com", "hunterdavis@uagateway.org",
    "daishadavis1998@gmail.com", "gryphonnevermind@gmail.com", "info@centercourtclub.com",
    "resources@hjtep.org", "xiaoxiaolong.crystal@gmail.com", "Seijifank@gmail.com", "ellyh@cpe2.org",
    "qteepie1212@aol.com", "Budzeyday@aol.com", "laura.brown@meditechgroup.com", "user9321@guerrillamail.com",
    "test8823@temp-mail.org", "guest1145@10minutemail.com", "demo7432@dropmail.me",
    "mailbot6590@maildrop.cc", "emily.johnson94@gmail.com", "michael.brooks21@yahoo.com",
    "sarah.taylor@outlook.com", "daniel.martinez83@hotmail.com", "laura.nguyen01@gmail.com", "googlecloud@google.com","security@getgitguardian.com","no-reply@accounts.google.com","support@github.com","honinghindus@gmail.com","lilaroyjggdgdgrtyrg@gmail.com","per@scrimba.com","resources@hjtep.org"
]+ user_spam
labels = [1]*10 + [0]*11 + [1]*5 + [0]*10 + [1]*3 +[0]*3

def get_training_data():
    global Emails,labels, user_spam
    Emails = Emails + user_spam
    labels = labels + [1] * len(user_spam)
    return Emails, labels

v = CountVectorizer()
x = v.fit_transform(Emails)
assert len(Emails) == len(labels), f"Email and label length mismatch: {len(Emails)} vs {len(labels)}"
x_train, x_test, y_train, y_test = train_test_split(x, labels, test_size=0.01)
model = DecisionTreeClassifier()
model.fit(x_train, y_train)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_client_secret_path():
    return resource_path("client_secret.json")  

def authenticate_gmail():
    from google.oauth2.credentials import Credentials

    creds = None
    token_path = os.path.join(pathlib.Path.home(), ".gmail_token.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(get_client_secret_path(), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            raise RuntimeError(f"OAuth Authentication failed: {e}")

    service = build('gmail', 'v1', credentials=creds)
    return service

def classify_emails():
    result_text.delete(1.0, tk.END)

    try:
        num_to_fetch = int(email_count_entry.get())
        if num_to_fetch <= 0:
            result_text.insert(tk.END, "Please enter a number greater than 0.\n")
            return
    except ValueError:
        result_text.insert(tk.END, "Invalid input. Enter a number.\n")
        return

    try:
        service = authenticate_gmail()
    except Exception as e:
        result_text.insert(tk.END, f"Auth Error: {e}\n")
        return

    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=num_to_fetch).execute()
        messages = results.get('messages', [])
    except Exception as e:
        result_text.insert(tk.END, f"Error accessing Gmail: {e}\n")
        return

    if not messages:
        result_text.insert(tk.END, "No emails found.\n")
        return

    email_list = []
    full_message_info = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload']['headers']
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        email_list.append(sender)
        full_message_info.append((msg['id'], sender))

    vectors = v.transform(email_list)
    predictions = model.predict(vectors)

    for (msg_id, sender), label in zip(full_message_info, predictions):
        status = "SPAM" if label == 1 else "NOT SPAM"
        result_text.insert(tk.END, f"{sender} => {status}\n")

        if label == 1:
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'addLabelIds': ['SPAM'], 'removeLabelIds': ['INBOX']}
            ).execute()
            result_text.insert(tk.END, "→ Moved to SPAM folder.\n")

        result_text.insert(tk.END, "\n")

root = tk.Tk()
root.title("Gmail Spam Classifier")
root.geometry("640x640")

top_frame = tk.Frame(root)
top_frame.pack(pady=10)

tk.Label(top_frame, text="Number of emails to scan:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
email_count_entry = tk.Entry(top_frame, width=5, font=("Arial", 12))
email_count_entry.pack(side=tk.LEFT)
email_count_entry.insert(0, "10")  

scan_btn = tk.Button(top_frame, text="Scan Inbox", command=classify_emails, font=("Arial", 12))
scan_btn.pack(side=tk.LEFT, padx=10)

result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25, font=("Courier", 10))
result_text.pack(pady=10)

userSpamFrame = tk.Frame(root)
userSpamFrame.pack(pady=5)
tk.Label(userSpamFrame, text="Report Email as Spam:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
userSpamEntry = tk.Entry(userSpamFrame, width=30, font=("Arial", 12))
userSpamEntry.pack(side=tk.LEFT)

def report_spam():
    email = userSpamEntry.get().rstrip()
    if email:
        user_spam.append(email)
        save_user_spam(user_spam)
        Emails, labels = get_training_data()
        global x_train, x_test, y_train, y_test, model, v
        x = v.fit_transform(Emails)
        x_train, x_test, y_train, y_test = train_test_split(x, labels, test_size=0.01)
        model.fit(x_train, y_train)
        result_text.insert(tk.END, f"{email} reported as SPAM and added to model.\n\n")
        userSpamEntry.delete(0, tk.END)
        spam_listbox.insert(tk.END, email)
tk.Button(userSpamFrame, text="Report Spam", command=report_spam, font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
spam_list_frame = tk.Frame(root)
spam_list_frame.pack(pady=10)

tk.Label(spam_list_frame, text="Reported Spam Emails:", font=("Arial", 12)).pack()

spam_listbox = tk.Listbox(spam_list_frame, width=50, font=("Courier", 10))
spam_listbox.pack()

def remove_selected_spam():
    selected = spam_listbox.curselection()
    if not selected:
        return
    index = selected[0]
    email = spam_listbox.get(index)
    spam_listbox.delete(index)

    if email in user_spam:
        user_spam.remove(email)
        save_user_spam(user_spam)
        Emails, labels = get_training_data()
        global x_train, x_test, y_train, y_test, model, v
        x = v.fit_transform(Emails)
        x_train, x_test, y_train, y_test = train_test_split(x, labels, test_size=0.01)
        model.fit(x_train, y_train)
        result_text.insert(tk.END, f"{email} removed from reported spam and model retrained.\n\n")

tk.Button(spam_list_frame, text="Remove Selected", command=remove_selected_spam, font=("Arial", 12)).pack(pady=5)

root.mainloop()
