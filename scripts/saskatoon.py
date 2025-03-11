import feedparser
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define the RSS feeds to monitor
feeds = [
    'https://sasktoday.ca/rss/north/saskatoon',
    'https://sasktoday.ca/rss/provincial-news/newsletter-provincial-news',
    'https://sasktoday.ca/rss/southwest/newsletter-southwest', 'https://sasktoday.ca/rss/southeast/newsletter-southeast',
    'https://sasktoday.ca/rss/north/newsletter-north', 'https://sasktoday.ca/rss/central/newsletter-central'
]


def get_articles_from_feed(feed_url):
    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    articles = []
    # Only take the latest 5 articles
    for entry in feed.entries[:5]:  # Limits to the first 5 articles
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'source': feed_url
        })
    return articles


def find_duplicates(all_items):
    seen = {}
    duplicates = []
    for item in all_items:
        if item['title'] in seen:
            seen[item['title']].append(item['source'])
            duplicates.append(item)
        else:
            seen[item['title']] = [item['source']]
    return duplicates, seen


def send_email(subject, body):
    # Get email credentials from environment variables
    sender_email = os.getenv("EMAIL_SENDER")
    recipient_emails = os.getenv(
        "EMAIL_RECIPIENTS")  # Should be a comma-separated list of emails
    email_password = os.getenv("EMAIL_PASSWORD")

    # Check if credentials are set
    print(f"Debug - Sender: {sender_email}")
    print(f"Debug - Recipients: {recipient_emails}")
    print(f"Debug - Password: {'[HIDDEN]' if email_password else 'Not set'}")

    if not all([sender_email, recipient_emails, email_password]):
        print(
            "Error: Missing email credentials. Please set EMAIL_SENDER, EMAIL_RECIPIENTS, and EMAIL_PASSWORD in Secrets."
        )
        return

    # Create message container
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_emails  # Comma-separated list of emails
    msg['Subject'] = subject

    # Attach the body to the message
    msg.attach(MIMEText(body, 'html'))

    try:
        # Setup the server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(sender_email, email_password)
        server.sendmail(sender_email, recipient_emails.split(','),
                        msg.as_string())  # Send to all recipients
        server.close()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")


def format_email_report(duplicates, all_items, seen):
    # Start with the HTML header and style
    body = """
    <html>
    <head>
    <style>
        body { font-family: Arial, sans-serif; }
        a.article-link { color: black !important; text-decoration: underline; }
        a.article-link.duplicate { font-weight: bold; }
        a.source-link { color: blue; text-decoration: none; padding: 5px; }
        .duplicate-source { color: blue; }
        ul { list-style-type: none; padding: 0; }
        li { margin-bottom: 15px; }
    </style>
    </head>
    <body>
    """

    body += "<h2>Saskatoon Today Newsletter - Duplicate Article Check</h2>"
    body += f"<p>Scanned {len(all_items)} articles and found {len(duplicates)} duplicates.</p>"

    # If there are duplicates, list them
    if duplicates:
        body += "<h4>Duplicate Articles Found:</h4><ul>"
        for dup in duplicates:
            sources = [
                f'<a href="{s}" class="source-link">{s}</a>'
                for s in seen[dup["title"]]
            ]
            body += f'<li><a href="{dup["link"]}" class="article-link duplicate">{dup["title"]}</a> (Found in: {",".join(sources)})</li>'
        body += "</ul>"
    else:
        body += "<p>No duplicates found.</p>"

    body += '<div style="margin-bottom: 20px;"></div>'

    # Now list all the articles that were checked
    body += "<p>Articles Checked:</p><ul>"
    for item in all_items:
        body += f'<li><a href="{item["link"]}" class="article-link">{item["title"]}</a><br>'
        body += f'Source: <a href="{item["source"]}" class="source-link">{item["source"]}</a></li>'
    body += "</ul></body></html>"

    return body


def run_monitor():
    all_items = []  # This will hold all articles from all feeds
    for feed_url in feeds:
        print(f"Checking feed: {feed_url}")
        articles = get_articles_from_feed(feed_url)
        all_items.extend(articles)

    # Find duplicates
    duplicates, seen = find_duplicates(all_items)

    # Format the email body
    email_body = format_email_report(duplicates, all_items, seen)

    # Send the email
    send_email("Duplicate Article Check - Saskatoon Today Newsletter", email_body)


if __name__ == "__main__":
    run_monitor()
