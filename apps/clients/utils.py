# apps/clients/utils.py

def get_client_payhead_columns(client, include_zero=False):
    """
    Get all payhead columns for a client
    - Returns: {'earnings': ['Bonus', 'DA', ...], 'deductions': ['Insurance', ...]}
    """
    from .models import ClientPayheadTemplate

    earnings = []
    deductions = []

    templates = ClientPayheadTemplate.objects.filter(
        client=client,
        is_active=True
    ).order_by('display_order')

    for template in templates:
        if template.type == 'EARNING':
            earnings.append(template.name)
        else:
            deductions.append(template.name)

    return {
        'earnings': earnings,
        'deductions': deductions
    }


def get_client_active_payheads(client, assignments):
    """
    Get payheads that have at least one employee with value > 0
    """
    payhead_columns = get_client_payhead_columns(client)

    active_earnings = []
    active_deductions = []

    # Check each payhead if any assignment has value > 0
    for payhead in payhead_columns['earnings']:
        has_value = False
        for assignment in assignments:
            if assignment.salary_heads.get('earnings', {}).get(payhead, 0) > 0:
                has_value = True
                break
        if has_value:
            active_earnings.append(payhead)

    for payhead in payhead_columns['deductions']:
        has_value = False
        for assignment in assignments:
            if assignment.salary_heads.get('deductions', {}).get(payhead, 0) > 0:
                has_value = True
                break
        if has_value:
            active_deductions.append(payhead)

    return {
        'earnings': active_earnings,
        'deductions': active_deductions
    }