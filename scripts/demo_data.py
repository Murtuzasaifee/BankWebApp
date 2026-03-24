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
        'country_code': 'KSA',
        'account_number': f'{APP_NAME}-SAV-77889900',
        'kyc_status': 'Completed',
        'accounts': [
            {
                'type': 'Savings Account',
                'balance': 8450.00,
                'account_number': 'SA894000000077889900',
                'account_type': 'Mada Savings Account',
                'account_status': 'Active',
                'branch_code': f'{APP_NAME}-RIY-102',
                'currency': 'SAR',
                'instrument_type': 'Mada Card',
                'instrument_id': 'DC-334455',
                'per_txn_limit': 5000.00,
                'daily_limit': 20000.00,
                'monthly_limit': 100000.00,
                'available_credit': None,
            },
            {
                'type': 'Debit Card',
                'balance': 2340.50,
                'account_number': 'DC-334455',
                'account_type': 'Mada Debit Card',
                'account_status': 'Active',
                'branch_code': f'{APP_NAME}-RIY-102',
                'currency': 'SAR',
                'instrument_type': 'Mada Card',
                'instrument_id': 'DC-334455',
                'per_txn_limit': 5000.00,
                'daily_limit': 20000.00,
                'monthly_limit': 100000.00,
                'available_credit': None,
            },
            {
                'type': 'Credit Card',
                'balance': 600.00,
                'account_number': 'CC-667788',
                'account_type': 'Credit Card',
                'account_status': 'Active',
                'branch_code': f'{APP_NAME}-RIY-102',
                'currency': 'SAR',
                'instrument_type': 'Credit Card',
                'instrument_id': 'CC-667788',
                'per_txn_limit': 15000.00,
                'daily_limit': 15000.00,
                'monthly_limit': 50000.00,
                'available_credit': 600.00,
            },
        ],
        'transactions': [
            {'merchant': 'Amazon KSA', 'date': 'Jan 14, 2026', 'time': '18:20', 'type': 'Debit Card', 'amount': -250.00, 'status': 'Failed', 'icon': 'shopping-cart', 'id': 'TXN-3003'},
            {'merchant': 'Carrefour', 'date': 'Jan 14, 2026', 'time': '13:40', 'type': 'Debit Card', 'amount': -200.00, 'status': 'Completed', 'icon': 'shopping-bag', 'id': 'TXN-3002'},
            {'merchant': 'Aramco', 'date': 'Jan 14, 2026', 'time': '09:15', 'type': 'Debit Card', 'amount': -200.00, 'status': 'Completed', 'icon': 'gas-pump', 'id': 'TXN-3001'},
            {'merchant': 'Hunger Station', 'date': 'Jan 13, 2026', 'time': '21:10', 'type': 'Credit Card', 'amount': -900.00, 'status': 'Completed', 'icon': 'cutlery', 'id': 'TXN-3004'},
            {'merchant': 'Noon KSA', 'date': 'Jan 13, 2026', 'time': '22:05', 'type': 'Credit Card', 'amount': -800.00, 'status': 'Failed', 'icon': 'shopping-cart', 'id': 'TXN-3005'}
        ],
        'employer': 'INTELLECT',
        'designation': 'SOFTWARE ENGINEER',
        'monthly_salary': 25000.00,
        'mobile': '+966-50-2847361',
        'address': 'B25, BUILDING NO 18, RIYADH'
    },
    'Ahmed Mansouri': {
        'password': 'password',
        'display_name': 'Ahmed Al Mansouri',
        'user_id': 'usr002',
        'country_code': 'UAE',
        'account_number': f'{APP_NAME}-SAL-123456789012',
        'kyc_status': 'Completed',
        'accounts': [
            {
                'type': 'Salary Account',
                'balance': 81749.00,
                'account_number': 'SA894000000123456789012',
                'account_type': 'Salary Account',
                'account_status': 'Active',
                'branch_code': f'{APP_NAME}-DXB-210',
                'currency': 'AED',
                'instrument_type': 'SADAD / Online Transfer',
                'instrument_id': 'OT-774433',
                'per_txn_limit': None,
                'daily_limit': 50000.00,
                'monthly_limit': 250000.00,
                'available_credit': None,
            },
            {
                'type': 'Debit Card',
                'balance': 15200.00,
                'account_number': 'DC-746406',
                'account_type': 'Debit Card',
                'account_status': 'Active',
                'branch_code': f'{APP_NAME}-DXB-210',
                'currency': 'AED',
                'instrument_type': 'Mada Card',
                'instrument_id': 'DC-746406',
                'per_txn_limit': 5000.00,
                'daily_limit': 20000.00,
                'monthly_limit': 100000.00,
                'available_credit': None,
            },
            {
                'type': 'Savings Account',
                'balance': 45000.00,
                'account_number': 'SA894000000045670000',
                'account_type': 'Savings Account',
                'account_status': 'Active',
                'branch_code': f'{APP_NAME}-DXB-210',
                'currency': 'AED',
                'instrument_type': 'Mada Card',
                'instrument_id': 'DC-746406',
                'per_txn_limit': 5000.00,
                'daily_limit': 20000.00,
                'monthly_limit': 100000.00,
                'available_credit': None,
            },
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
        'mobile': '+966-50-2847361',
        'address': 'B25, BUILDING NO 18, BUTINA AREA, RIYADH'
    }
}
