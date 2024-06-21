import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from scraper import main

# Create directory for configs if it doesn't exist
config_dir = 'config'
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

accounts_file = os.path.join(config_dir, 'accounts.json')

# Check if accounts file exists, if not create an empty one
if not os.path.exists(accounts_file):
    with open(accounts_file, 'w') as file:
        json.dump({}, file)

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Maps Scraper GUI")
        self.create_widgets()
        self.load_accounts()

    def create_widgets(self):
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(pady=10)

        # Google Search Query
        self.query_label = tk.Label(self.input_frame, text="Google Search Query:")
        self.query_label.grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.query_entry = tk.Entry(self.input_frame, width=50)
        self.query_entry.grid(row=0, column=1, padx=10, pady=5)

        # Number of Emails to Send
        self.num_emails_label = tk.Label(self.input_frame, text="Number of Emails to Send:")
        self.num_emails_label.grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.num_emails_entry = tk.Entry(self.input_frame, width=50)
        self.num_emails_entry.grid(row=1, column=1, padx=10, pady=5)

        # Email Subject Line
        self.email_subject_label = tk.Label(self.input_frame, text="Email Subject Line:")
        self.email_subject_label.grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.email_subject_entry = tk.Entry(self.input_frame, width=50)
        self.email_subject_entry.grid(row=2, column=1, padx=10, pady=5)

        # Load existing sender account
        self.account_label = tk.Label(self.input_frame, text="Select Sender Account:")
        self.account_label.grid(row=3, column=0, padx=10, pady=5, sticky='e')
        self.account_combobox = ttk.Combobox(self.input_frame)
        self.account_combobox.grid(row=3, column=1, padx=10, pady=5)

        # Add new account button
        self.new_account_button = tk.Button(self.input_frame, text="Add New Account", command=self.add_new_account)
        self.new_account_button.grid(row=4, columnspan=2, pady=10)

        # Start scraping button
        self.start_button = tk.Button(self.input_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=5, columnspan=2, pady=20)

    def load_accounts(self):
        with open(accounts_file, 'r') as file:
            self.accounts = json.load(file)
            self.account_combobox['values'] = list(self.accounts.keys())

    def add_new_account(self):
        def save_account():
            email = email_entry.get()
            password = password_entry.get()
            type_ = "Outlook" if outlook_var.get() else "Gmail"
            self.accounts[email] = {"password": password, "type": type_}
            with open(accounts_file, 'w') as file:
                json.dump(self.accounts, file)
            self.load_accounts()
            new_acc_window.destroy()

        new_acc_window = tk.Toplevel(self.root)
        new_acc_window.title("Add New Sender Account")

        tk.Label(new_acc_window, text="Email:").grid(row=0, column=0, padx=10, pady=10)
        email_entry = tk.Entry(new_acc_window, width=30)
        email_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(new_acc_window, text="Password:").grid(row=1, column=0, padx=10, pady=10)
        password_entry = tk.Entry(new_acc_window, width=30, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)

        outlook_var = tk.BooleanVar(value=True)
        tk.Radiobutton(new_acc_window, text="Outlook", variable=outlook_var, value=True).grid(row=2, column=0, padx=10, pady=10)
        tk.Radiobutton(new_acc_window, text="Gmail", variable=outlook_var, value=False).grid(row=2, column=1, padx=10, pady=10)

        save_button = tk.Button(new_acc_window, text="Save Account", command=save_account)
        save_button.grid(row=3, columnspan=2, pady=10)

    def start_scraping(self):
        query = self.query_entry.get()
        num_emails = int(self.num_emails_entry.get())
        email_subject = self.email_subject_entry.get()
        sender_account = self.account_combobox.get()

        if sender_account not in self.accounts:
            messagebox.showerror("Error", "Please select a valid sender account.")
            return

        sender_info = self.accounts[sender_account]
        sender_info['email'] = sender_account  # Ensure the email key is added

        self.input_frame.pack_forget()  # Hide the input frame

        # Create the analytics dashboard
        self.dashboard_frame = tk.Frame(self.root)
        self.dashboard_frame.pack(pady=10)

        self.sending_account_label = tk.Label(self.dashboard_frame, text=f"Account: {sender_account}")
        self.sending_account_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')

        self.total_urls_scraped_label = tk.Label(self.dashboard_frame, text="Total URLs Scraped: 0")
        self.total_urls_scraped_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')

        self.total_emails_collected_label = tk.Label(self.dashboard_frame, text="Total Emails Collected: 0")
        self.total_emails_collected_label.grid(row=3, column=0, padx=10, pady=5, sticky='w')

        self.total_emails_delivered_label = tk.Label(self.dashboard_frame, text="Total Emails Delivered: 0")
        self.total_emails_delivered_label.grid(row=4, column=0, padx=10, pady=5, sticky='w')

        self.scraper_progress_label = tk.Label(self.dashboard_frame, text="Scraper Progress: 0%")
        self.scraper_progress_label.grid(row=5, column=0, padx=10, pady=5, sticky='w')

        self.email_outreach_progress_label = tk.Label(self.dashboard_frame, text="Email Outreach Progress: 0%")
        self.email_outreach_progress_label.grid(row=6, column=0, padx=10, pady=5, sticky='w')

        self.progress_bar = ttk.Progressbar(self.dashboard_frame, orient="horizontal", mode="indeterminate", length=300)
        self.progress_bar.grid(row=7, column=0, padx=10, pady=20)
        self.progress_bar.start()

        self.update_dashboard(num_emails)

        def run_scraper():
            try:
                main(query, num_emails, email_subject, sender_info, self.update_dashboard)
            except KeyError as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            finally:
                self.progress_bar.stop()
                self.dashboard_frame.pack_forget()  # Hide the dashboard frame
                self.input_frame.pack(pady=10)  # Show the input frame again

        threading.Thread(target=run_scraper).start()

    def update_dashboard(self, num_emails, total_urls_scraped=0, total_emails_collected=0, total_emails_delivered=0):
        self.total_urls_scraped_label.config(text=f"Total URLs Scraped: {total_urls_scraped}")
        self.total_emails_collected_label.config(text=f"Total Emails Collected: {total_emails_collected}")
        self.total_emails_delivered_label.config(text=f"Total Emails Delivered: {total_emails_delivered}")

        scraper_progress = int((total_emails_collected / num_emails) * 100) if num_emails > 0 else 0
        email_outreach_progress = int((total_emails_delivered / num_emails) * 100) if num_emails > 0 else 0

        self.scraper_progress_label.config(text=f"Scraper Progress: {scraper_progress}%")
        self.email_outreach_progress_label.config(text=f"Email Outreach Progress: {email_outreach_progress}%")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
