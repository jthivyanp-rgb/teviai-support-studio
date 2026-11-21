"""Fictional sample enquiries.

All names, order numbers, emails and phone numbers are invented.
- Emails use the reserved example.com domain.
- Phone numbers use the UK 07700 900xxx range reserved for fiction.
- The card number 4111 1111 1111 1111 is a well-known public test number.
These same messages are used by the automated tests in tests/test_cases.py.
"""

SAMPLE_ENQUIRIES = [
    {
        "case_id": "TC01",
        "customer_name": "Arun Kumar",
        "channel": "Email",
        "message": "Hi, I ordered a candle set (order A1043) last week but I've changed my mind. "
                   "Can I get my money back?",
    },
    {
        "case_id": "TC02",
        "customer_name": "Meena Shah",
        "channel": "Website form",
        "message": "My parcel was supposed to arrive on Monday and it still isn't here. "
                   "Could you send me the tracking number please?",
    },
    {
        "case_id": "TC03",
        "customer_name": "Tom Fielding",
        "channel": "Instagram DM",
        "message": "Do your soy candles contain any nut oils? My daughter has a nut allergy.",
    },
    {
        "case_id": "TC04",
        "customer_name": "Priya Raman",
        "channel": "Email",
        "message": "Please update my card, the new number is 4111 1111 1111 1111, expiry 09/28. "
                   "My email is priya.r@example.com in case you need it.",
    },
    {
        "case_id": "TC05",
        "customer_name": "Gareth Lloyd",
        "channel": "Email",
        "message": "The lamp arrived broken and honestly this is the worst service I've ever had. "
                   "If I don't hear back today I will contact my lawyer.",
    },
    {
        "case_id": "TC06",
        "customer_name": "Sofia Marin",
        "channel": "Website form",
        "message": "Do the ceramic mugs come with a warranty? Are they dishwasher safe? "
                   "Also, do you ship internationally?",
    },
    {
        "case_id": "TC07",
        "customer_name": "Kavitha Selvam",
        "channel": "Facebook message",
        "message": "What time does your shop open on Saturdays?",
    },
    {
        "case_id": "TC08",
        "customer_name": "Unknown sender",
        "channel": "Website chat",
        "message": "Hello? Is anyone there?",
    },
    {
        "case_id": "TC09",
        "customer_name": "Daniel Okafor",
        "channel": "Email",
        "message": "I want a full refund AND compensation for my ruined weekend. "
                   "You need to promise this will never happen again.",
    },
    {
        "case_id": "TC10",
        "customer_name": "Lena Hoffmann",
        "channel": "Email",
        "message": "Please delete my account and all the personal data you hold about me. "
                   "You can call me on 07700 900456 to confirm.",
    },
]
