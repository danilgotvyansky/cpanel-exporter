# cPanel Exporter
The **cPanel Exporter** is a Prometheus exporter for cPanel account. It scrapes the Statistics panel, MySQL, PostGreSQL, FTP and email accounts information using cPanel's built-in UAPI.

## Table of Contents
1. [Getting Started](#getting-started)
    - [Installation](#installation)
        - [Running as Python Application](#running-as-python-application)
    - [Usage](#usage)
    - [Overview](#overview)
    - [Dashboard](#dashboard)
2. [Contribution](#contribution)

## Getting Started

### Installation

#### Running as Python Application

Follow the steps below to run the **cPanel Exporter** as a Python application:

1. Navigate to the Create Python App menu in your cPanel to create a Python application. This will set up a virtual environment with Python inside your cPanel.

2. Copy the virtual environment activation command provided by cPanel and execute it in the Terminal.

3. Download the source code from this repository to your working directory.

4. Install the required packages. This application requires only Flask. You can install it by running the following command:

    ```
    pip install -r requirements.txt
    ```
5. Execute the script either in the background or as it is. See [Usage](#usage) for more details and available flags.

    ```
    python cpanel-exporter.py
    ```

### Usage

This application serves an endpoint on the HTTP route `/metrics` which returns the scraped cPanel data in plaintext suitable for Prometheus to consume.

On startup, the app will serve a metrics endpoint on your specified port (default `9123`). You can configure it using the `-P` or `--port` flag. For instance:

```
python cpanel-exporter.py -P 9124
```

This will start the cPanel Exporter on port `9124`.

In your Prometheus configuration, you must add a new target for this endpoint as follows:

```
scrape_configs:
  - job_name: 'cpanel'
    static_configs:
      - targets: ['<your-cpanel-domain-or-ip>:9124']
```

---
### Overview
cPanel account exporter scrapes the information from the Statistics panel, MySQL, PostGreSQL, email and FTP accounts for the particular cPanel account using [cPanel built-in UAPI](https://api.docs.cpanel.net/openapi/cpanel/overview/). Can be run inside any cPanel account unless it supports UAPI.

Below there is a list of commands you can execute on your cPanel account to check if the exporter is supported:

<details> 
 <summary>Commands</summary>

   ```
   uapi --output=jsonpretty \
   StatsBar \
   get_stats display='bandwidthusage|diskusage|addondomains|autoresponders|cachedlistdiskusage|cachedmysqldiskusage|cpanelversion|emailaccounts|emailfilters|emailforwarders|filesusage|ftpaccounts|hostingpackage|hostname|kernelversion|machinetype|operatingsystem|mailinglists|mysqldatabases|mysqldiskusage|mysqlversion|parkeddomains|perlversion|phpversion|shorthostname|sqldatabases|subdomains|cachedpostgresdiskusage|postgresqldatabases|postgresdiskusage'
   ```
   
   ```
   uapi --output=jsonpretty \
   ResourceUsage \
   get_usages
   ```
   
   ```
   uapi --output=jsonpretty \
   Postgresql \
   list_databases
   ```
   
   ```
   uapi --output=jsonpretty \
   Mysql \
   list_databases
   ```
   
   ```
   uapi --output=jsonpretty \
   Email \
   list_pops_with_disk
   ```

   ```
   uapi --output=jsonpretty \
   Ftp \
   list_ftp_with_disk
   ```

   ```
   uapi --output=jsonpretty \
   Variables \
   get_user_information
   ```

</details>


- All metrics are appended with the relevant labels.
- There are also `.*free.*` and `.*percent.*` metrics for some resources and most of them are calculated within the code. 

The list of generated metrics:

<details> 
 <summary>Metrics</summary>

   ```
   cpanel_bandwidthusage 1191570309.12
   cpanel_free_diskusage 18083741696.0
   cpanel_free_diskusage_percent 84.0
   cpanel_diskusage_percent 16.0
   cpanel_diskusage 3391094784.0
   cpanel_addondomains 0.0
   cpanel_autoresponders 0.0
   cpanel_cachedlistdiskusage 0.0
   cpanel_cachedmysqldiskusage 15118336.0
   cpanel_emailaccounts 2.0
   cpanel_emailfilters 0.0
   cpanel_emailforwarders 0.0
   cpanel_free_filesusage 246811.0
   cpanel_free_filesusage_percent 82.0
   cpanel_filesusage_percent 18.0
   cpanel_filesusage 53189.0
   cpanel_ftpaccounts 1.0
   cpanel_mailinglists 0.0
   cpanel_mysqldatabases 4.0
   cpanel_mysqldiskusage 15118336.0
   cpanel_parkeddomains 0.0
   cpanel_sqldatabases 4.0
   cpanel_subdomains 4.0
   cpanel_postgresqldatabases 0.0
   cpanel_info {cpanelversion="110.0 (build 15)",hostingpackage="somepackage,hostname="some.server.com",kernelversion="2.6.32-954.3.5.lve1.4.90.el6.x86_64",machinetype="x86_64",operatingsystem="linux",mysqlversion="10.6.17-MariaDB-cll-lve",perlversion="5.10.1",shorthostname="someserver",user="cpaneluser",ip="162.0.0.0"} 1
   cpanel_cpu_percent 13.0
   cpanel_cpu 26.0
   cpanel_ep 0.0
   cpanel_memphy_percent 22.11
   cpanel_memphy 237350912.0
   cpanel_iops 1.0
   cpanel_io 4096.0
   cpanel_nproc 45.0
   cpanel_mysql_db_disk_usage{db="db_name"} 2363392
   cpanel_email_disk_usage{email="someemail@domain.com"} 87763
   cpanel_ftp_account_disk_usage{ftp_account="ftp_account@domain.com"} 87763
   ```

</details>

---
### Dashboard

Feel free to use this dashboard designed specially for this exporter:
[https://grafana.com/grafana/dashboards/20801](https://grafana.com/grafana/dashboards/20801)

<details> 
 <summary>Screenshots</summary>

![screenshot1](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/ce316e0f-cd72-436f-8375-7d676ae6049c)
![screenshot2](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/63173174-b07a-458c-8f0d-c828e5fdce06)
![screenshot3](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/e2249473-25e6-4f4d-abcc-0714f0bd6ef0)
![screenshot4](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/59c2333c-9642-4738-9d4f-99c0acbbe01b)
![screenshot5](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/3511274a-ea3b-4753-8df5-d3dea8e5474b)
![screenshot6](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/3203d349-a779-4b92-bd9c-0725c48e6bae)
![screenshot7](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/77fb67ab-ca55-4874-856f-4a5f61bb6846)
![screenshots8](https://github.com/danilgotvyansky/cpanel-exporter/assets/122215118/7e6d04ed-92fb-4938-9bfa-a94f098ecaf3)

</details>

---

## Contribution
If you are a Prometheus expert or just know Python, please feel free to contribute to this project, submit a pull request, issue, or suggestion. I appreciate all the help and ideas!

---

That's it! If you encounter any problems or have questions, feel free to open an issue.
