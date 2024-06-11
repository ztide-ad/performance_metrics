from django.shortcuts import render, redirect
from django.db import connection
import pandas as pd

def get_month_number(month_name):
    month_name_to_number = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    return month_name_to_number.get(month_name.capitalize(), 1)

def get_data(query, params):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)

def create_user_link(assigned_to_id, assigned_to_name, fixed_version_name, year, quarter=None, month=None):
    if month:
        return f'<a href="/user_issues/?assigned_to_id={assigned_to_id}&fixed_version_name={fixed_version_name}&year={year}&quarter={quarter}&month={month}">{assigned_to_name}</a>'
    elif quarter:
        return f'<a href="/user_issues/?assigned_to_id={assigned_to_id}&fixed_version_name={fixed_version_name}&year={year}&quarter={quarter}">{assigned_to_name}</a>'
    else:
        return f'<a href="/user_issues/?assigned_to_id={assigned_to_id}&fixed_version_name={fixed_version_name}&year={year}">{assigned_to_name}</a>'

def dashboard(request):
    project_name = request.GET.get('project_name', 'BidAssist')
    fixed_version_name = request.GET.get('fixed_version_name', 'BidAssist-Issues')
    year = request.GET.get('year', 2023)
    quarter = request.GET.get('quarter', 1)
    month_name = request.GET.get('month_name', 'January')
    month = get_month_number(month_name)

    query_temp_table = '''
    CREATE TEMPORARY TABLE temp_custom_values AS
    SELECT customized_id, value
    FROM custom_values
    WHERE custom_field_id = 69;
    CREATE INDEX idx_customized_id ON temp_custom_values(customized_id);
    '''

    with connection.cursor() as cursor:
        cursor.execute(query_temp_table)

    query_year = '''
    SELECT 
        issues.assigned_to_id,
        CONCAT(users.firstname, ' ', users.lastname) AS assigned_to_name,
        YEAR(issues.updated_on) AS year,
        COALESCE(SUM(temp_custom_values.value), 0) AS points_assigned_yearly,
        COALESCE(SUM(CASE WHEN issues.status_id = 3 THEN temp_custom_values.value ELSE 0 END), 0) AS points_completed_yearly
    FROM issues
    LEFT JOIN users ON issues.assigned_to_id = users.id
    LEFT JOIN versions ON issues.fixed_version_id = versions.id
    LEFT JOIN projects ON issues.project_id = projects.id
    LEFT JOIN temp_custom_values ON issues.id = temp_custom_values.customized_id
    WHERE 
        projects.name = %s
        AND versions.name = %s
        AND YEAR(issues.updated_on) = %s
    GROUP BY 
        issues.assigned_to_id, 
        YEAR(issues.updated_on)
    ORDER BY 
        issues.assigned_to_id, 
        YEAR(issues.updated_on);
    '''

    query_quarter = '''
    SELECT 
        issues.assigned_to_id,
        CONCAT(users.firstname, ' ', users.lastname) AS assigned_to_name,
        YEAR(issues.updated_on) AS year,
        QUARTER(issues.updated_on) AS quarter,
        COALESCE(SUM(temp_custom_values.value), 0) AS points_assigned_quarterly,
        COALESCE(SUM(CASE WHEN issues.status_id = 3 THEN temp_custom_values.value ELSE 0 END), 0) AS points_completed_quarterly
    FROM issues
    LEFT JOIN users ON issues.assigned_to_id = users.id
    LEFT JOIN versions ON issues.fixed_version_id = versions.id
    LEFT JOIN projects ON issues.project_id = projects.id
    LEFT JOIN temp_custom_values ON issues.id = temp_custom_values.customized_id
    WHERE 
        projects.name = %s
        AND versions.name = %s
        AND YEAR(issues.updated_on) = %s
        AND QUARTER(issues.updated_on) = %s
    GROUP BY 
        issues.assigned_to_id, 
        YEAR(issues.updated_on),
        QUARTER(issues.updated_on)
    ORDER BY 
        issues.assigned_to_id, 
        YEAR(issues.updated_on), 
        QUARTER(issues.updated_on);
    '''

    query_month = '''
    SELECT 
        issues.assigned_to_id,
        CONCAT(users.firstname, ' ', users.lastname) AS assigned_to_name,
        YEAR(issues.updated_on) AS year,
        QUARTER(issues.updated_on) AS quarter,
        MONTH(issues.updated_on) AS month,
        COALESCE(SUM(temp_custom_values.value), 0) AS points_assigned_monthly,
        COALESCE(SUM(CASE WHEN issues.status_id = 3 THEN temp_custom_values.value ELSE 0 END), 0) AS points_completed_monthly
    FROM issues
    LEFT JOIN users ON issues.assigned_to_id = users.id
    LEFT JOIN versions ON issues.fixed_version_id = versions.id
    LEFT JOIN projects ON issues.project_id = projects.id
    LEFT JOIN temp_custom_values ON issues.id = temp_custom_values.customized_id
    WHERE 
        projects.name = %s
        AND versions.name = %s
        AND YEAR(issues.updated_on) = %s
        AND QUARTER(issues.updated_on) = %s
        AND MONTH(issues.updated_on) = %s
    GROUP BY 
        issues.assigned_to_id, 
        YEAR(issues.updated_on),
        QUARTER(issues.updated_on),
        MONTH(issues.updated_on)
    ORDER BY 
        issues.assigned_to_id, 
        YEAR(issues.updated_on), 
        QUARTER(issues.updated_on),
        MONTH(issues.updated_on);
    '''

    df_year = get_data(query_year, [project_name, fixed_version_name, year])
    df_quarter = get_data(query_quarter, [project_name, fixed_version_name, year, quarter])
    df_month = get_data(query_month, [project_name, fixed_version_name, year, quarter, month])

    df_year['assigned_to_name'] = df_year.apply(lambda row: create_user_link(row['assigned_to_id'], row['assigned_to_name'], fixed_version_name, year), axis=1)
    df_quarter['assigned_to_name'] = df_quarter.apply(lambda row: create_user_link(row['assigned_to_id'], row['assigned_to_name'], fixed_version_name, year, quarter), axis=1)
    df_month['assigned_to_name'] = df_month.apply(lambda row: create_user_link(row['assigned_to_id'], row['assigned_to_name'], fixed_version_name, year, quarter, month), axis=1)

    context = {
        'df_year': df_year.to_html(classes='table table-striped', escape=False),
        'df_quarter': df_quarter.to_html(classes='table table-striped', escape=False),
        'df_month': df_month.to_html(classes='table table-striped', escape=False),
    }

    return render(request, 'dashboard/dashboard.html', context)

def user_issues(request):
    assigned_to_id = request.GET.get('assigned_to_id')
    fixed_version_name = request.GET.get('fixed_version_name', 'BidAssist-Issues')
    year = request.GET.get('year', 2023)
    quarter = request.GET.get('quarter')
    month = request.GET.get('month')
    sort_story_points = request.GET.get('sort_story_points', 'false').lower() == 'true'

    order_by_clause = 'story_point DESC' if sort_story_points else 'issues.id'

    if month:
        query = f'''
        SELECT
            issues.assigned_to_id,
            issues.id,
            issues.subject,
            custom_values.value AS story_point,
            COALESCE(bug_counts.bug_count, 0) AS bug_count
        FROM issues
        LEFT JOIN versions ON issues.fixed_version_id = versions.id
        LEFT JOIN custom_values ON issues.id = custom_values.customized_id AND custom_values.custom_field_id = 69
        LEFT JOIN (
            SELECT parent_id, COUNT(*) AS bug_count
            FROM issues AS bugs
            WHERE bugs.parent_id IS NOT NULL
            GROUP BY parent_id
        ) AS bug_counts ON issues.id = bug_counts.parent_id
        WHERE
            issues.assigned_to_id = %s
            AND versions.name = %s
            AND YEAR(issues.updated_on) = %s
            AND QUARTER(issues.updated_on) = %s
            AND MONTH(issues.updated_on) = %s
            AND issues.status_id = 3
        ORDER BY {order_by_clause};
        '''
        params = [assigned_to_id, fixed_version_name, year, quarter, month]
    elif quarter:
        query = f'''
        SELECT
            issues.assigned_to_id,
            issues.id,
            issues.subject,
            custom_values.value AS story_point,
            COALESCE(bug_counts.bug_count, 0) AS bug_count
        FROM issues
        LEFT JOIN versions ON issues.fixed_version_id = versions.id
        LEFT JOIN custom_values ON issues.id = custom_values.customized_id AND custom_values.custom_field_id = 69
        LEFT JOIN (
            SELECT parent_id, COUNT(*) AS bug_count
            FROM issues AS bugs
            WHERE bugs.parent_id IS NOT NULL
            GROUP BY parent_id
        ) AS bug_counts ON issues.id = bug_counts.parent_id
        WHERE
            issues.assigned_to_id = %s
            AND versions.name = %s
            AND YEAR(issues.updated_on) = %s
            AND QUARTER(issues.updated_on) = %s
            AND issues.status_id = 3
        ORDER BY {order_by_clause};
        '''
        params = [assigned_to_id, fixed_version_name, year, quarter]
    else:
        query = f'''
        SELECT
            issues.assigned_to_id,
            issues.id,
            issues.subject,
            custom_values.value AS story_point,
            COALESCE(bug_counts.bug_count, 0) AS bug_count
        FROM issues
        LEFT JOIN versions ON issues.fixed_version_id = versions.id
        LEFT JOIN custom_values ON issues.id = custom_values.customized_id AND custom_values.custom_field_id = 69
        LEFT JOIN (
            SELECT parent_id, COUNT(*) AS bug_count
            FROM issues AS bugs
            WHERE bugs.parent_id IS NOT NULL
            GROUP BY parent_id
        ) AS bug_counts ON issues.id = bug_counts.parent_id
        WHERE
            issues.assigned_to_id = %s
            AND versions.name = %s
            AND YEAR(issues.updated_on) = %s
            AND issues.status_id = 3
        ORDER BY {order_by_clause};
        '''
        params = [assigned_to_id, fixed_version_name, year]

    df_issues = get_data(query, params)

    context = {
        'df_issues': df_issues.to_html(classes='table table-striped'),
    }

    return render(request, 'dashboard/user_issues.html', context)

def home(request):
    return redirect('dashboard')

