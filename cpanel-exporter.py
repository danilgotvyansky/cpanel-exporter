import subprocess
import json
import argparse
from flask import Flask, Response

app = Flask(__name__)


def fetch_cpanel_metrics():
    """Fetches general metrics data from cPanel. It then parses the output as JSON and extracts the metrics data."""
    cmd = ['uapi', '--output=json', 'StatsBar', 'get_stats',
           'display=bandwidthusage|diskusage|addondomains|autoresponders|cachedlistdiskusage|cachedmysqldiskusage'
           '|cpanelversion|emailaccounts|emailfilters|emailforwarders|filesusage|ftpaccounts|hostingpackage|hostname'
           '|kernelversion|machinetype|operatingsystem|mailinglists|mysqldatabases|mysqldiskusage|mysqlversion'
           '|parkeddomains|perlversion|phpversion|shorthostname|sqldatabases|subdomains|cachedpostgresdiskusage'
           '|postgresqldatabases|postgresdiskusage']
    result = subprocess.run(cmd, capture_output=True, text=True)

    data = result.stdout
    parsed_data = json.loads(data)
    metrics = parsed_data['result']['data']

    return metrics


def construct_labels(metrics):
    """This function constructs the labels string from metric items, including user and IP."""
    user_ip_cmd = ['uapi', '--output=json', 'Variables', 'get_user_information']
    user_ip_result = subprocess.run(user_ip_cmd, capture_output=True, text=True)

    user_ip_data = json.loads(user_ip_result.stdout)
    user = user_ip_data['result']['data']['user']
    ip = user_ip_data['result']['data']['ip']

    labels_dict = {}
    for item in metrics:
        if 'value' in item and isinstance(item['value'], str) and item['name'] not in ['diskusage', 'bandwidthusage']:
            labels_dict[item['name']] = item['value'].replace('"', '\\"')

    labels_dict['user'] = user
    labels_dict['ip'] = ip

    return ",".join(f'{key}="{value}"' for key, value in labels_dict.items())


def fetch_resource_usage_metrics():
    """Fetches resource usage (CPU, MEM, processes,etc.) metrics data from cPanel. It then parses the output as JSON
    and extracts the resource metrics data."""
    cmd = ['uapi', '--output=json', 'ResourceUsage', 'get_usages']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        app.logger.error("Error executing uapi for Resource Usage metrics: " + result.stderr)
        return []

    resource_data = json.loads(result.stdout)

    if resource_data['result']['status'] == 0 and resource_data['result']['errors']:
        error_message = resource_data['result']['errors'][0]
        app.logger.error(f"Error fetching resource usage metrics: {error_message}")
        return []

    resource_metrics = resource_data['result']['data']
    if resource_metrics is None:
        app.logger.warning("No Resource usage data found.")
        return []

    return resource_metrics


def format_resource_usage_metrics(resource_metrics, labels_string):
    """Formats resource usage metrics by extracting relevant information from the input data and constructing
    formatted strings for each metric."""
    formatted_metrics_output = []
    for metric in resource_metrics:
        metric_id = metric['id']
        usage = metric['usage']
        maximum = metric.get('maximum')
        if metric_id in ['lvecpu', 'lveep', 'lvememphy', 'lveiops', 'lveio', 'lvenproc']:
            metric_value = float(usage)
            metric_name = f"cpanel_{metric_id[3:]}"
            if metric_id in ['lvecpu', 'lvememphy'] and maximum:
                metric_percent = round((metric_value / float(maximum)) * 100, 2)
                formatted_metrics_output.append(
                    f"{metric_name}_percent{{{labels_string}}} {metric_percent}")
            formatted_metrics_output.append(
                f"{metric_name}{{{labels_string}}} {metric_value}")

    return formatted_metrics_output


def fetch_mysql_db_metrics():
    """Fetches mysql database metrics data from cPanel. It then parses the output as JSON and extracts the mysql
    database metrics data."""
    cmd = ['uapi', '--output=json', 'Mysql', 'list_databases']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        app.logger.error("Error executing uapi for MySQL database metrics: " + result.stderr)
        return []

    mysql_db_data = json.loads(result.stdout)

    if mysql_db_data['result']['status'] == 0 and mysql_db_data['result']['errors']:
        error_message = mysql_db_data['result']['errors'][0]
        if "You do not have the feature" in error_message:
            app.logger.warning(f"MySQL feature unavailable: {error_message}")
            return []

    mysql_db_metrics = mysql_db_data['result']['data']
    if mysql_db_metrics is None:
        app.logger.warning("No MySQL databases found or the feature is disabled.")
        return []

    return mysql_db_metrics


def format_mysql_db_metrics(mysql_db_metrics, labels_string):
    """Formats mysql database metrics by extracting relevant information from the input data and constructing
    formatted strings the metric."""
    mysql_db_metrics_output = []
    for db in mysql_db_metrics:
        database_name = db['database']
        disk_usage_bytes = db['disk_usage']

        formatted_metric = f"cpanel_mysql_db_disk_usage{{db=\"{database_name}\",{labels_string}}} {disk_usage_bytes}"
        mysql_db_metrics_output.append(formatted_metric)

    return mysql_db_metrics_output


def fetch_postgres_db_metrics():
    """Fetches postgresql database metrics data from cPanel. It then parses the output as JSON and extracts the
    postgresql database metrics data."""
    cmd = ['uapi', '--output=json', 'Postgresql', 'list_databases']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        app.logger.error("Error executing uapi for PostgreSQL database metrics: " + result.stderr)
        return []

    pg_data = json.loads(result.stdout)

    if pg_data['result']['status'] == 0 and pg_data['result']['errors']:
        error_message = pg_data['result']['errors'][0]
        if "You do not have the feature" in error_message:
            app.logger.warning(f"PostgreSQL feature unavailable: {error_message}")
            return []

    pg_metrics = pg_data['result']['data']
    if pg_metrics is None:
        app.logger.warning("No PostgreSQL databases found or the feature is disabled.")
        return []

    return pg_metrics


def format_postgres_db_metrics(pg_metrics, labels_string):
    """Formats postgresql database metrics by extracting relevant information from the input data and constructing
    formatted strings the metric."""
    pg_metrics_output = []
    for db in pg_metrics:
        database_name = db['database']
        disk_usage_bytes = db['disk_usage']

        formatted_metric = f"cpanel_postgres_db_disk_usage{{db=\"{database_name}\",{labels_string}}} {disk_usage_bytes}"
        pg_metrics_output.append(formatted_metric)

    return pg_metrics_output


def fetch_email_metrics():
    """Fetches email metrics data from cPanel. It then parses the output as JSON and extracts the email metrics data."""
    cmd = ['uapi', '--output=json', 'Email', 'list_pops_with_disk']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        app.logger.error("Error executing uapi for Email accounts metrics: " + result.stderr)
        return []

    email_data = json.loads(result.stdout)

    if email_data['result']['status'] == 0 and email_data['result']['errors']:
        error_message = email_data['result']['errors'][0]
        if "You do not have the feature" in error_message:
            app.logger.warning(f"Email accounts feature unavailable: {error_message}")
            return []

    email_metrics = email_data['result']['data']
    if email_metrics is None:
        app.logger.warning("No Email accounts found or the feature is disabled.")
        return []

    return email_metrics


def format_email_metrics(email_metrics, labels_string):
    """Formats email metrics by extracting relevant information from the input data and constructing formatted
    strings for the metric."""
    email_metrics_output = []
    for email_info in email_metrics:
        email = email_info['email']
        disk_used_bytes = int(email_info['_diskused'])

        formatted_metric = f"cpanel_email_disk_usage{{email=\"{email}\",{labels_string}}} {disk_used_bytes}"
        email_metrics_output.append(formatted_metric)

    return email_metrics_output


def fetch_ftp_metrics():
    """Fetches ftp metrics data from cPanel. It then parses the output as JSON and extracts the ftp metrics data."""
    cmd = ['uapi', '--output=json', 'Ftp', 'list_ftp_with_disk']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stderr:
        app.logger.error("Error executing uapi for Email accounts metrics: " + result.stderr)
        return []

    ftp_data = json.loads(result.stdout)

    if ftp_data['result']['status'] == 0 and ftp_data['result']['errors']:
        error_message = ftp_data['result']['errors'][0]
        if "You do not have the feature" in error_message:
            app.logger.warning(f"FTP accounts feature unavailable: {error_message}")
            return []

    ftp_metrics = ftp_data['result']['data']
    if ftp_metrics is None:
        app.logger.warning("No FTP accounts found or the feature is disabled.")
        return []

    return ftp_metrics


def format_ftp_metrics(ftp_metrics, labels_string):
    """Formats ftp metrics by extracting relevant information from the input data and constructing formatted strings
    for the metric."""
    ftp_metrics_output = []
    for ftp_info in ftp_metrics:
        ftp = ftp_info['login']
        disk_used_mb = float(ftp_info['_diskused'])
        disk_used_bytes = int(disk_used_mb * 1024 * 1024)

        formatted_metric = f"cpanel_ftp_account_disk_usage{{ftp_account=\"{ftp}\",{labels_string}}} {disk_used_bytes}"
        ftp_metrics_output.append(formatted_metric)

    return ftp_metrics_output


@app.route('/metrics')
def metrics():
    """Flask route that generates and returns metrics data in the Prometheus format. It fetches various metrics from
    cPanel using the `fetch_cpanel_metrics` function and constructs labels based on the metrics data and user
    information. It then formats the numeric metrics and resource usage metrics using helper functions and combines
    them into a single response."""
    try:
        metrics = fetch_cpanel_metrics()
        numeric_metrics_output = []
        labels_string = construct_labels(metrics)

        for item in metrics:
            metric_name = 'cpanel_' + item['name']
            metric_value = item.get('_count') or item.get('value')

            if metric_value.isdigit() or (isinstance(metric_value, str) and metric_value.replace('.', '', 1).isdigit()):
                metric_value = float(metric_value)

            if item['name'] not in ['mysqldiskusage', 'cachedmysqldiskusage', 'postgresdiskusage',
                                    'cachedpostgresdiskusage']:
                if 'units' in item:
                    if item['units'] == "GB":
                        metric_value *= 1024 ** 3
                    elif item['units'] == "MB":
                        metric_value *= 1024 ** 2
            if item['name'] in ['diskusage', 'filesusage'] and 'percent' in item:
                percent = float(item['percent'])
                percent_free = 100 - percent

            if item['name'] in ['diskusage', 'filesusage']:
                max_value = item.get('_max')
                if max_value and max_value.lower() != "unlimited":
                    if item['name'] == 'diskusage':
                        max_value = float(max_value) * 1024 * 1024
                    else:
                        max_value = float(max_value)

                if max_value and isinstance(max_value, float) and isinstance(metric_value, float):
                    free_value = max_value - metric_value
                    numeric_metrics_output.append(f"cpanel_free_{item['name']}{{{labels_string}}} {free_value}")
                    numeric_metrics_output.append(
                        f"cpanel_free_{item['name']}_percent{{{labels_string}}} {percent_free}")
                    numeric_metrics_output.append(f"cpanel_{item['name']}_percent{{{labels_string}}} {percent}")

            if isinstance(metric_value, (float, int)):
                formatted_metric = f"{metric_name}{{{labels_string}}} {metric_value}"
                numeric_metrics_output.append(formatted_metric)

        info_metric = f'cpanel_info{{{labels_string}}} 1'
        numeric_metrics_output.append(info_metric)

        metrics_response = '\n'.join(numeric_metrics_output)

        resource_metrics = fetch_resource_usage_metrics()
        resource_metrics_output = format_resource_usage_metrics(resource_metrics, labels_string)
        resource_metrics_response = '\n'.join(resource_metrics_output)

        mysql_db_metrics = fetch_mysql_db_metrics()
        mysql_db_metrics_output = format_mysql_db_metrics(mysql_db_metrics, labels_string)
        mysql_db_metrics_response = '\n'.join(mysql_db_metrics_output)

        pg_metrics = fetch_postgres_db_metrics()
        pg_metrics_output = format_postgres_db_metrics(pg_metrics, labels_string)
        pg_metrics_response = '\n'.join(pg_metrics_output)

        email_metrics = fetch_email_metrics()
        email_metrics_output = format_email_metrics(email_metrics, labels_string)
        email_metrics_response = '\n'.join(email_metrics_output)

        ftp_metrics = fetch_ftp_metrics()
        ftp_metrics_output = format_ftp_metrics(ftp_metrics, labels_string)
        ftp_metrics_response = '\n'.join(ftp_metrics_output)

        combined_metrics_response = '\n'.join(
            [metrics_response, resource_metrics_response, mysql_db_metrics_response, email_metrics_response,
             pg_metrics_response, ftp_metrics_response])

        return Response(combined_metrics_response, mimetype='text/plain')
    except Exception as e:
        app.logger.error(f"Failed to generate metrics: {str(e)}")
        return Response("Internal server error", status=500, mimetype='text/plain')


def parse_arguments():
    """Sets up an argument parser with a description and a default value for the port argument. It then returns the
    parsed arguments."""
    parser = argparse.ArgumentParser(
        description='cPanel Exporter for Prometheus. Scrapes the Statistics panel, MySQL, PostGreSQL and email '
                    'accounts information using cPanel built-in UAPI.')
    parser.add_argument('-P', '--port', type=int, default=9123, help='Port to serve the exporter on. Default is 9123.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    app.run(host='0.0.0.0', port=args.port)
