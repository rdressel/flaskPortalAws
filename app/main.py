# main.py

import boto3
from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user

# ACCOUNTS=[(]'lafawsus_ro','lhamnonp_ro','lhamsbox_ro','lhamshare_ro','lhlaprod_ro','lhlanonp_ro','lhlasbox_ro']
# ACCOUNTS = ['lhamsbox_ro', 'lhlasbox_ro']
ACCOUNTS = ['lhamsbox_ro', 'lhlasbox_ro']
global report_data
report_data = {}


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


@main.route('/<string:page_name>')
def html_page(page_name):
    """
    Dynamic html pages
    """
    return render_template(page_name)


@main.route('/reports-<string:report_name>')
def report_page(report_name):
    """
    Dynamic html reports
    """
    flash(f'Running {report_name}')
    if report_name == 'ec2instances':
        report_data, report_title = get_ec2instances()
    else:
        # Report not defined
        return render_template('error.html', data='Report not found...', report_title="Report not found")
    if len(report_data) > 0:
        first_item = list(report_data.keys())[0]
        report_columns = []
        for key, value in report_data[first_item].items():
            report_columns.append(key)
        return render_template('run-reports.html', report_data=report_data, report_columns=report_columns,
                               report_title=report_title)
    else:
        return render_template('error.html', data='No data to be processed.', report_title=report_title)


def get_tag(tag_name, tags):
    """
    Get tag key value.
    :param tag_name: Tag name to lookup.
    :param tags: Key, value list from resource.
    :return: Tag value.
    """
    tagvalue = ''
    if tags is not None:  # Test for NoneType
        for tag in tags:
            if tag["Key"] == tag_name:
                tagvalue = tag["Value"]
    return tagvalue


def get_iam_profile(instance_id, session):
    """
    Get IAM Profile for Ec2 instances.
    :param instance_id: Instance ID to lookup.
    :param session: AWS session to use.
    :return: IAM profile name.
    """
    ec2 = session.client('ec2')
    try:
        response = ec2.describe_iam_instance_profile_associations(
            Filters=[
                {
                    'Name': 'instance-id',
                    'Values': [instance_id]
                }
            ]
        )
        if response['IamInstanceProfileAssociations']:
            profile = response['IamInstanceProfileAssociations'][0]['IamInstanceProfile']['Arn']
            profile = profile[profile.find('/') + 1:]  # strip only name
        else:
            profile = "none assigned"
    except ec2.exceptions.ClientError as error:
        profile = "error during lookup" + error
    return profile


def get_ec2instances():
    """
    Get Ec2 instances.
    :return report_data: Dict to generate report.
    :return report_title: HTML title to use.
    """
    report_title = 'Ec2 Instances by Account'
    for account in ACCOUNTS:
        session = boto3.Session(profile_name=account)
        ec2 = session.resource('ec2')
        for instance in ec2.instances.all():
            report_data[instance.id] = {
                'AWS Account': account,
                'Instance ID': instance.id,
                'Project Tag': get_tag('Project', instance.tags),
                'Name Tag': get_tag('Name', instance.tags),
                'Type': instance.instance_type,
                'State': instance.state['Name'],
                'Private IP': instance.private_ip_address,
                'Public IP': instance.public_ip_address,
                'IAM Profile': get_iam_profile(instance.id, session),
                'Launch Time': instance.launch_time,
            }
    return report_data, report_title
