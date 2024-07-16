
# Dashboard

This repository contains the backend of a dashboard built using the Django framework.

## Prerequisite

### 1. Start Redmine and MySQL Docker Containers

```bash
docker start <redmine_container_id_or_name> <mysql_container_name_or_id>
```

### 2. Create Story points
Given that initially story points had not been created we have to first create story points in the redmine server 

- Login as admin
- Go to Administration section 
- Then go to Custom Fields
- Click on New Custom Field 
- Select Issues 
- Click on Next 
- Set Format as Integer
- In the Trackers section, Select Bug, Feature, Enchancement, Task, Support
- In the Projects section, Select For all Projects
- Lastly Click on Create button

### 3. Assign Story Points
Since story points have not been issued for issues initial we will randomly assign story points to the already created issues through mysql database so as to not trigger the time-entry API and mess up the last_updated column of issues table. For this follow the following steps:

#### I. Access MySQL Database through Docker
To access the MySQL database through Docker, execute the following command:

```bash 
docker exec -it <mysql_container_name> bash
```

#### II. Go to MySQL Command Line
```bash
mysql -u <db_username> -p
```
Then enter the password of db_username

#### III. Select the Redmine Database
```sql
USE <db_name>;
```

#### IV. Identify the customized_id assigned to story point custom field

```sql
SELECT * FROM custom_values;
```
From the table generated identify the custom_field_id of story point custom field. For me it was 69, if it is different for you change it in the following queries

#### V. Assign Random Story Points

In the MySQL command line write an query to randomly assign values to customized_id which is the foreign key that links to issue id. Example:
```sql
INSERT INTO custom_values (customized_type, customized_id, custom_field_id, value)
SELECT 'Issue', issues.id, 69, FLOOR(1 + RAND() * 10)
FROM issues
LEFT JOIN custom_values ON issues.id = custom_values.customized_id AND custom_values.custom_field_id = 69
WHERE custom_values.customized_id IS NULL;
```
Now the database is set up for running the django project


## Django Setup Instructions

### 1. Go to the directory

``` bash
cd employee-productivity
```

### 2. Create a Virtual Environment

Create a virtual environment for the project:
``` bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

- on Ubuntu:

``` bash
source venv/Scripts/activate
```

### 4. Install Dependencies

Install the required libraries

``` python
pip install django==<compatible_version_with_sql>
pip install pandas
pip install mysqlclient
```
The docker image I was using to host Bitnami redmine had MySQL version 5.7.22  thus I had to install django version 4.1 though latest version of django will require MySQL version 8 or later.

### 5. Configure the Database

Open the `settings.py` file located under the `analytics` project directory and enter the details of your database configuration. 

```python
DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_name',
        'USER': 'db_username',
        'PASSWORD': 'db_password',
        'HOST': 'db_host',
        'PORT': 'db_port',
    }
}
```
### 6. Make Migrations

Make migrations for database changes

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 7. Run the Server

Run the Django project on any port I am using 8080


```bash
python3 manage.py runserver 8080
```
