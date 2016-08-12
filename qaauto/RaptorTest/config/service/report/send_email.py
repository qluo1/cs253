import subprocess
from subprocess import Popen, PIPE

REPORT_TMPL = r"""
<html>
        <head>
            <title>Raptor Test Report Page</title>
            <meta name="generator" content="HTMLReporter 0.0.2"/>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>

        <style type="text/css" media="screen,print">
        table, td, th{
            border: 1px solid #000;
            padding: 1px;
        }
        th{
            text-align:left;
        }
        .success{
            background-color:green;
            font-weight: bold;
        }

        .fail{
            background-color: red;
            font-weight: bold;
        }

        .warn{
            background-color: yellow;
            font-weight: bold;
        }

        .remove{
            background-color: #CC6666;
            font-weight: bold;
        }

        .add{
            background-color:#CCFF99;
            font-weight: bold;
        }
        </style>
        </head>
        <body>
            <h2>%(title)s</h2>
            <hr>
            <h2> Summary </h2>
            <table class="table">
                <thead>
                <tr>
                 <th>App</th>
                 <th>Total</th>
                 <th>Passed</th>
                 <th>Failed</th>
                 <th>Errors</th>
                 <th>Success Rate(ex skipped)</th>
                 <th>Date/Time</th>
                 <th>Duration</th>
                </tr>
                </thead>
                <tbody>
                <tr class=%(table_style)s>
                   <td>%(app)s</td>
                   <td>%(total)s</td>
                   <td>%(pass)s</td>
                   <td>%(fail)s</td>
                   <td>%(error)s</td>
                   <td>%(rate)s</td>
                   <td>%(dtime)s</td>
                   <td>%(duration)s</td>
                </tr>
                </tbody>
            </table>
            <hr>
            <h2> Break Down by Class </h2>
            <table class="table">
                <thead>
                <tr>
                 <th>Class</th>
                 <th>Total</th>
                 <th>Passed</th>
                 <th>Failed</th>
                 <th>Errors</th>
                </tr>
                </thead>
                <tbody>
                %(cls_result)s
                </tbody>
            </table>
            <hr/>
        <p>For detailed report, please find them in attached HTML file</p>

        </body>
        </html>
"""

CLS_RESULT_TMPL = r"""
                <tr class=%(table_style)s>
                   <td>%(name)s</td>
                   <td>%(count)s</td>
                   <td>%(pass)s</td>
                   <td>%(fail)s</td>
                   <td>%(error)s</td>
                </tr>
"""

def send(from_address,to_address, cc_address, subject_str, content_str, attachment_str):
    boundary = '=====================boundary========================'
    proc = subprocess.Popen(["/usr/sbin/sendmail","-t"], stdin=subprocess.PIPE)
    proc.stdin.write("To: %s \n" % to_address)
    proc.stdin.write("From: %s \n" % from_address)
    proc.stdin.write("cc: %s \n" % cc_address)
    proc.stdin.write("Subject: %s \n" % subject_str)
    proc.stdin.write("Mime-Version: 1.0 \n")
    proc.stdin.write('Content-Type: multipart/alternative; boundary=%s \n' % boundary)
    proc.stdin.write('--'+boundary + '\n')
    proc.stdin.write("Content-Type: text/html \n")
    proc.stdin.write(content_str)
    proc.stdin.write('\n')
    proc.stdin.write('--'+boundary + '\n')
    proc.stdin.write('Content-Type:application/octet-stream; name=test_report.html \n')
    proc.stdin.write('Content-Transfer-Encoding:base64 \n')
    proc.stdin.write('Content-Disposition: attachment; filename=test_report.html \n')
    proc.stdin.write('\n')
    proc.stdin.write(attachment_str)
    proc.stdin.write('\n')
    proc.stdin.write('--'+boundary + '--\n')
    proc.stdin.close()
    proc.wait()

def send_email(report_attrs, summary, attachment_str):
    cls_table = ''
    for cls_result in summary['class_summary']:
        if cls_result['error'] == 0 and cls_result['fail'] == 0:
            cls_result['table_style'] = 'add'
        else:
            cls_result['table_style'] = 'remove'
        cls_table += CLS_RESULT_TMPL % cls_result

    if report_attrs['fail'] == 0 and report_attrs['error'] == 0:
        report_attrs['table_style'] = 'add'
    else:
        report_attrs['table_style'] = 'remove'
    report_attrs['cls_result'] = cls_table
    content = REPORT_TMPL % dict(
            report_attrs    
        )
    send('eric.zhao@hk.email.gs.com', 'eric.zhao@hk.email.gs.com', '', 'Raptor Raw Test Report', content, attachment_str)

if __name__ == '__main__':
    content_str = ''
    with open('summary.html', 'r') as f:
        for line in f:
            content_str += line
    send('eric.zhao@hk.email.gs.com', 'eric.zhao@hk.email.gs.com', '', 'Test Report', content_str)

