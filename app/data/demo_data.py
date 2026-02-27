"""
Demo user data for Bank Web Application.
"""

from app.core.config import get_settings

settings = get_settings()
APP_NAME = settings.APP_NAME

DISPLAY_NAME = 'User'

USERS = {
    'Mohammed Faisal': {
        'password': 'password',
        'display_name': 'Mohammed Faisal',
        'user_id': 'usr001',
        'customer_id': f'{APP_NAME}-CUST-459812',
        'account_number': f'{APP_NAME}-SAV-77889900',
        'accounts': [
            {'type': 'Savings Account', 'balance': 8450.00, 'number': f'{APP_NAME}-SAV-••••9900'},
            {'type': 'Debit Card', 'balance': 2340.50, 'number': 'DC-334455'},
            {'type': 'Credit Card', 'balance': 600.00, 'number': 'CC-667788'}
        ],
        'transactions': [
            {'merchant': 'Amazon KSA', 'date': 'Jan 14, 2026', 'time': '18:20', 'type': 'Debit Card', 'amount': -250.00, 'status': 'Failed', 'icon': 'shopping-cart', 'id': 'TXN-3003'},
            {'merchant': 'Carrefour', 'date': 'Jan 14, 2026', 'time': '13:40', 'type': 'Debit Card', 'amount': -200.00, 'status': 'Completed', 'icon': 'shopping-bag', 'id': 'TXN-3002'},
            {'merchant': 'Aramco', 'date': 'Jan 14, 2026', 'time': '09:15', 'type': 'Debit Card', 'amount': -200.00, 'status': 'Completed', 'icon': 'gas-pump', 'id': 'TXN-3001'},
            {'merchant': 'Hunger Station', 'date': 'Jan 13, 2026', 'time': '21:10', 'type': 'Credit Card', 'amount': -900.00, 'status': 'Completed', 'icon': 'cutlery', 'id': 'TXN-3004'},
            {'merchant': 'Noon KSA', 'date': 'Jan 13, 2026', 'time': '22:05', 'type': 'Credit Card', 'amount': -800.00, 'status': 'Failed', 'icon': 'shopping-cart', 'id': 'TXN-3005'}
        ]
    },
    'Ahmed Al Mansouri': {
        'password': 'password',
        'display_name': 'Ahmed Al Mansouri',
        'user_id': 'usr002',
        'customer_id': f'{APP_NAME}-CUST-289034',
        'account_number': f'{APP_NAME}-SAL-123456789012',
        'accounts': [
            {'type': 'Salary Account', 'balance': 81749.00, 'number': f'{APP_NAME}-SAL-••••9012'},
            {'type': 'Debit Card', 'balance': 15200.00, 'number': 'DC-746406'},
            {'type': 'Savings Account', 'balance': 45000.00, 'number': f'{APP_NAME}-SAV-••••4567'}
        ],
        'transactions': [
            {'merchant': 'ATM Cash Withdrawal', 'date': 'Dec 30, 2025', 'time': '16:45', 'type': 'Debit Card', 'amount': -1000.00, 'status': 'Completed', 'icon': 'money-bill-wave', 'id': 'TXN-8001'},
            {'merchant': 'Fuel Station', 'date': 'Dec 28, 2025', 'time': '08:30', 'type': 'Debit Card', 'amount': -100.00, 'status': 'Completed', 'icon': 'gas-pump', 'id': 'TXN-8002'},
            {'merchant': 'Hunger Station', 'date': 'Dec 27, 2025', 'time': '20:15', 'type': 'Debit Card', 'amount': -70.00, 'status': 'Completed', 'icon': 'utensils', 'id': 'TXN-8003'},
            {'merchant': 'Coffee Shop POS', 'date': 'Dec 26, 2025', 'time': '09:00', 'type': 'Debit Card', 'amount': -18.00, 'status': 'Completed', 'icon': 'coffee', 'id': 'TXN-8004'},
            {'merchant': 'Salary Credit - Asharqia Tech', 'date': 'Dec 25, 2025', 'time': '00:01', 'type': 'Salary', 'amount': 35000.00, 'status': 'Completed', 'icon': 'arrow-down', 'id': 'TXN-8005'}
        ],
        'employer': 'ASHARQIA TECH SOLUTIONS',
        'designation': 'SOFTWARE ENGINEER',
        'monthly_salary': 35000.00,
        'emirates_id': '784-123-1234567-1',
        'mobile': '+971-50-2847361',
        'address': 'B25, BUILDING NO 18, BUTINA AREA, SHARJAH'
    }
}


# Demo applications data for Admin panel
APPLICATIONS = [
    {
        'application_id': 'APP-20260115-001',
        'applicant_name': 'Mohammed Faisal',
        'user_id': 'usr001',
        'submission_date': 'Jan 15, 2026',
        'status': 'Completed',
        'application_type': 'Personal Loan',
        'application_html_url': 'https://pf-gtm-general-purpose.s3.amazonaws.com/reports/2026-02-26_06-13-42.html?AWSAccessKeyId=AKIAYS2NUQM2E5HG5N7I&Signature=Ht7YQ0VHYCVlNo5JW9SmrMu29%2BE%3D&Expires=1772691222'
    },
    {
        'application_id': 'APP-20260120-002',
        'applicant_name': 'Ahmed Al Mansouri',
        'user_id': 'usr002',
        'submission_date': 'Jan 20, 2026',
        'status': 'In Progress',
        'application_type': 'Home Loan',
        'application_html_url': 'https://www.w3.org/WAI/demos/bad/after/home.html'
    },
    {
        'application_id': 'APP-20260125-003',
        'applicant_name': 'Sara Al Khaldi',
        'user_id': 'usr003',
        'submission_date': 'Jan 25, 2026',
        'status': 'Pending',
        'application_type': 'Auto Loan',
        'application_html_url': 'https://www.w3.org/WAI/demos/bad/after/home.html'
    },
    {
        'application_id': 'APP-20260201-004',
        'applicant_name': 'Khalid Al Rashid',
        'user_id': 'usr004',
        'submission_date': 'Feb 01, 2026',
        'status': 'Pending',
        'application_type': 'Personal Loan',
        'application_html_url': 'https://www.w3.org/WAI/demos/bad/after/home.html'
    },
    {
        'application_id': 'APP-20260205-005',
        'applicant_name': 'Fatima Al Zahra',
        'user_id': 'usr005',
        'submission_date': 'Feb 05, 2026',
        'status': 'In Progress',
        'application_type': 'Home Loan',
        'application_html_url': 'https://www.w3.org/WAI/demos/bad/after/home.html'
    },
    {
        'application_id': 'APP-20260210-006',
        'applicant_name': 'Omar Hassan',
        'user_id': 'usr006',
        'submission_date': 'Feb 10, 2026',
        'status': 'Completed',
        'application_type': 'Auto Loan',
        'application_html_url': 'https://www.w3.org/WAI/demos/bad/after/home.html'
    },
    {
        'application_id': 'APP-20260215-007',
        'applicant_name': 'Nour Al Din',
        'user_id': 'usr007',
        'submission_date': 'Feb 15, 2026',
        'status': 'Pending',
        'application_type': 'Personal Loan',
        'application_html_url': 'https://www.w3.org/WAI/demos/bad/after/home.html'
    }
]
