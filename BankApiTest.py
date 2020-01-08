import os
import sys
import ConfigParser
from hashlib import sha256
import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

conf_path = os.path.dirname(os.path.abspath(__file__)) + "\conf.ini"


class BankApiTest(object):
    def __init__(self, url, port=None):
        self.url = url
        self.port = port
        self.conf = ConfigParser.ConfigParser()
        self.conf.read(conf_path)
        self.phone = self.get_conf("userinfo", "phone")
        self.cardid = self.get_conf("userinfo", "cardid")
        self.name = self.get_conf("userinfo", "name")
        self.degree = int(self.get_conf("userinfo", "degree"))
        self.appid = self.get_conf("signatureinfo", "appid")
        self.appidsecret = self.get_conf("signatureinfo", "appid")
        self.headers = {"Content-Type": "application/json"}
        self.service_list = ["gybankcreditscore", "netagequery", "degreecheck",
                             "multiloan", "idbaseinfo", "gybankriskdecision"]
        # self.service_list = ["gybankcreditscore"]

    def get_conf(self, section, name):
        return self.conf.get(section, name)

    def __sign(self, value):
        sign = sha256(value).hexdigest()
        if sign:
            return sign
        else:
            return None

    def generate_param(self, service):
        param = {}
        if service == 'gybankcreditscore':
            value = self.phone + self.appidsecret
            signature = self.__sign(value)
            param = dict(zip(("phone", "cardid", "name", "appid", "signature"),
                             (self.phone, self.cardid, self.name, self.appid, signature)))
        elif service == 'netagequery':
            value = self.phone + self.appidsecret
            signature = self.__sign(value)
            param = dict(zip(("phone", "cardid", "name", "appid", "signature"),
                             (self.phone, self.cardid, self.name, self.appid, signature)))
        elif service == 'degreecheck':
            value = self.cardid + self.name + str(self.degree) + self.appidsecret
            signature = self.__sign(value)
            param = dict(zip(("cardid", "name", "degree", "appid", "signature"),
                             (self.cardid, self.name, self.degree, self.appid, signature)))
        elif service == 'multiloan':
            value = self.phone + self.cardid + self.name + self.appidsecret
            signature = self.__sign(value)
            param = dict(zip(("phone", "cardid", "name", "appid", "signature"),
                             (self.phone, self.cardid, self.name, self.appid, signature)))
        elif service == 'idbaseinfo':
            value = self.cardid + self.appidsecret
            signature = self.__sign(value)
            param = dict(zip(("cardid", "appid", "signature"),
                             (self.cardid, self.appid, signature)))
        elif service == 'gybankriskdecision':
            value = self.cardid + self.name + self.phone + self.appidsecret
            signature = self.__sign(value)
            param = dict(zip(("phone", "cardid", "name", "appid", "signature"),
                             (self.phone, self.cardid, self.name, self.appid, signature)))
        return json.dumps(param)

    def api_post(self, service, param):
        if self.port is None:
            new_url = self.url + '/' + service
        else:
            new_url = self.url + ':' + str(self.port) + '/' + service
        response = requests.post(new_url, param, headers=self.headers)
        return response

    def run(self):
        html = '''
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <title>[BankApiTest]-Report</title>
            </head>
            <body>
            '''
        infohtml = ''
        endhtml = '</body></html>'
        for service in self.service_list:
            try:
                post_param = self.generate_param(service)
                res = self.api_post(service, post_param)
                url = res.url
                # print res.status_code
                assert res.status_code == 200, "\n Run (%s) test FAIL, status_code: %s" % (service, res.status_code)
                print "\n Run (%s) test OK, status_code: %s" % (service, res.status_code)
                result = res.json()
            except Exception as err:
                print str(err)
                result = res.json()
            finally:
                infohtml += '<p> URL: %s <br /> importParam: %s <br /> outParam: %s <br /></p>' % (url, post_param.decode('unicode_escape'), result)
        self.send_mail(html+infohtml+endhtml)

    def send_mail(self, text):
        sender = self.get_conf("mail", "sender")
        receiver = self.get_conf("mail", "receiver")
        subject = '[BankApiTest]-Report-%s' % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        smtpserver = self.get_conf("mail", "smtpserver")
        username = self.get_conf("mail", "username")
        password = self.get_conf("mail", "password")
        msg = MIMEText(text, 'html', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender
        msg['To'] = ''.join(receiver)
        smtp = smtplib.SMTP()
        smtp.connect(smtpserver)
        smtp.login(username, password)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()

if __name__ == '__main__':
    if len(sys.argv) > 2:
        bank_api = BankApiTest(sys.argv[1], sys.argv[2])
        bank_api.run()
    elif len(sys.argv) == 2:
        bank_api = BankApiTest(sys.argv[1])
        bank_api.run()
