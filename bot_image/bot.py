import logging
import os
from dotenv import load_dotenv
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import paramiko
import psycopg2
from psycopg2 import Error

text_help = '''
I can help you find certain information in text, check the complexity of passwords, and monitor Linux systems. 
I also repeat any text entered. If you send me the text, I'll repeat it.

You can control me by sending these commands:
/start - start this bot
/help - get help message

Search Information:
/find_email - search email Addesses in input text
/find_phone_number - search phone numbers in input text

Check password:
/verify_password - check password complexity

Monitoring Linux-system:
/get_release - get information about os release 
/get_uname - get information About the processor architecture, system hostname, and kernel version
/get_uptime - get system uptime
/get_df - get information about the file system status
/get_free - get information about the status of RAM
/get_mpstat - get information about system performance
/get_w - get current active user
/get_auths - get last ten (10) logins
/get_critical - get information about 5 critical events
/get_ps - get information about running processes
/get_ss - get information about the ports in use
/get_apt_list - get information about installed packages
/get_services - get information about running services

DataBase get information:
/get_repl_logs - get database replication logs
/get_emails - get information about email addesses
/get_phone_numbers - get information about phone numbers
'''

# Подключаем логирование
logging.basicConfig(
    filename='tg_bot_logs.txt',
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    encoding="utf-8",
    filemode='w'
)
logger = logging.getLogger(__name__)

# Инициализация переменных из .env файла.
load_dotenv()
token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')

sshHost = os.getenv('SSH_HOST')
sshPort = os.getenv('SSH_PORT')
sshUsername = os.getenv('SSH_USER')
sshPassword = os.getenv('SSH_PASSWORD')

dbHost = os.getenv('DB_HOST')
dbPort = os.getenv('DB_PORT')
dbUsername = os.getenv('DB_USER')
dbPass = os.getenv('DB_PASSWORD')
dbDefaultName = os.getenv('DB_DEFAULT_NAME')
dbConnectName = os.getenv('DB_CONNECT_NAME')

logger.debug(f'token = {token}')
logger.debug(f'chat_id = {chat_id}')
logger.debug(f'sshHost = {sshHost}')
logger.debug(f'sshUsername = {sshUsername}')
logger.debug(f'sshPassword = {sshPassword}')
logger.debug(f'dbUsername = {dbUsername}')
logger.debug(f'dbPass = {dbPass}')
logger.debug(f'dbHost = {dbHost}')
logger.debug(f'dbPort = {dbPort}')
logger.debug(f'dbDefaultName = {dbDefaultName}')
logger.debug(f'dbConnectName = {dbConnectName}')
logger.info(f'Variable values from the .ENV file are loaded.')

def start(update: Update, context):
    user = update.effective_user
    logger.info(f'Executed command /start.')
    update.message.reply_text(
        f'Hello, {user.full_name}!\nYou can see the available functions by running the /help command.')


def helpcommand(update: Update, context):
    update.message.reply_text(f'{text_help}')
    logger.info(f'Executed command /help.')


def echo(update: Update, context):
    user_input = update.message.text
    update.message.reply_text(user_input)
    logger.info(f'Executed echo function. User input:\n{user_input}')


def findphonenumbersCommand(update: Update, context):
    update.message.reply_text('Enter text to search for phone numbers:')
    logger.info(f'Executed command /find_phone_number.')
    return 'findphonenumbers'


def findphonenumbers(update: Update, context):
#    global phoneNumberList
    user_input = update.message.text  # Получаем текст, содержащий(или нет) номера телефонов
    logger.debug(f'User Input:\n{user_input}')
    # Далее регулярному выражению соответствуют форматы телефонных номеров из тестового текста ниже
    # Формат телефонного номера: 80000000000
    # Формат телефонного номера: 8(000)0000000
    # Формат телефонного номера: 8 000 000 00 00
    # Формат телефонного номера: 8 (000) 000 00 00
    # Формат телефонного номера: 8-000-000-00-00
    # Формат телефонного номера: 8 (000) 000-00-00
    # Формат телефонного номера: +70000000000
    # Формат телефонного номера: +7(000)0000000
    # Формат телефонного номера: +7 000 000 00 00
    # Формат телефонного номера: +7 (000) 000 00 00
    # Формат телефонного номера: +7-000-000-00-00
    # Формат телефонного номера: +7 (000) 000-00-00
    phoneNumRegex = re.compile(r'(?:\+7|8)-?\s?\(?\d{3}\)?\s?-?\d{3}-?\s?\d{2}-?\s?\d{2}')
    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов
    context.user_data['PhoneNumList'] = phoneNumberList
    logger.debug(f'Type of phoneNumberList: {type(phoneNumberList)}')
    logger.debug(f'Value of phoneNumberList: {phoneNumberList}')

    if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Phone numbers not found.')
        logger.info('Phone numbers not found')
        return ConversationHandler.END  # Завершаем выполнение функции

    phoneNumbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i + 1}. {phoneNumberList[i]}\n'  # Записываем очередной номер
    logger.debug(f'Result converted to string:\n{phoneNumbers}')

    # Отправляем сообщение пользователю
    update.message.reply_text(f'Search results of phone numbers in input text:\n{phoneNumbers}')
    logger.info(f'Search results of phone numbers in input text:\n{phoneNumbers}')

    # Отправляем сообщение пользователю
    update.message.reply_text(text='Save the result to a database? Enter: yes or no.')
    return 'savePhoneNumbers'


def savePhoneNumbers(update: Update, context):
    user_input = update.message.text
    logger.debug(f'User Input:\n{user_input}')
    try:
        if user_input == 'yes':
            # for item in phoneNumberList:
            for item in context.user_data['PhoneNumList']:
                tmpResult = getDataFromDB(user=dbUsername,
                                          password=dbPass,
                                          host=dbHost,
                                          port=dbPort,
                                          database=dbConnectName,
                                          query=f"SELECT \"number\" FROM public.phone_numbers WHERE number='{item}';")
                logger.debug(f'Result of SELECT query:\n{tmpResult}')

                if not tmpResult:
                    changeDataFromDB(user=dbUsername,
                                     password=dbPass,
                                     host=dbHost,
                                     port=dbPort,
                                     database=dbConnectName,
                                     query=f"INSERT INTO public.phone_numbers(\"number\") VALUES ('{item}');")
                    logger.info(f'Result of SELECT query:\n{tmpResult}')
                    update.message.reply_text(f'Phone number {item} saved to database.')
                else:
                    update.message.reply_text(f'The phone number {item} is already in the database. Not saved.')

        elif user_input == 'no':
            update.message.reply_text(f'The found phone numbers are not saved in the database. Close the conversation.')
            logger.info(f'The found phone numbers are not saved in the database')
            return ConversationHandler.END
        else:
            update.message.reply_text(f'Unexpected input. Close the conversation.')
            logger.info(f'Unexpected input. Close the conversation.')
            return ConversationHandler.END
    except Exception as e:
        logger.error(f'Error: {e}')

    return ConversationHandler.END


def findEmailAddressesCommand(update: Update, context):
    update.message.reply_text('Enter text to search for email addresses:')
    logger.info(f'Executed command /get_emails.')
    return 'findEmailAddresses'


def findEmailAddresses(update: Update, context):
    # global emailAddressList
    user_input = update.message.text  # Получаем текст, содержащий(или нет) email адреса
    logger.debug(f'User Input:\n{user_input}')
    # Далее регулярному выражению соответствуют форматы адресов электронной почты из тестового текста ниже
    # Формат email адреса: myemailaddress@gmail.com
    # Формат email адреса: my-emai-lad-dress@gmail.com
    # Формат email адреса: t.test@test.com
    # Формат email адреса: test_test@test.com
    # Формат email адреса: test@test.test.com
    # Формат email адреса: t.test123@test.com
    # Формат email адреса: test123_test@test.com
    # Формат email адреса: test123@test.test.com
    #   emailAddrRegex = re.compile(r'(?:[\w.-]+)@(?:[\w.-]+)\.(?:[\w.-]+)')
    emailAddrRegex = re.compile(r'[-_a-zA-Z0-9.]{3,64}@(?:[A-za-z0-9-]{3,63}\.){1,3}[A-Za-z]{2,15}')
    emailAddressList = emailAddrRegex.findall(user_input)  # Ищем номера телефонов
    context.user_data['EmailList'] = emailAddressList
    logger.debug(f'Type of emailAddressList: {type(emailAddressList)}')
    logger.debug(f'Value of emailAddressList: {emailAddressList}')

    if not emailAddressList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Email адреса не найдены')
        logger.info('Email address not found')
        return ConversationHandler.END  # Завершаем выполнение функции

    emailAddresses = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(emailAddressList)):
        emailAddresses += f'{i + 1}. {emailAddressList[i]}\n'  # Записываем очередной номер
    logger.debug(f'Result converted to string:\n{emailAddresses}')

    update.message.reply_text(
        f'Search results of mail addresses in input text:\n{emailAddresses}')  # Отправляем сообщение пользователю
    logger.info(f'Search results of mail addresses in input text:\n{emailAddresses}')

    # Отправляем сообщение пользователю
    update.message.reply_text(text='Save the result to a database? Enter: yes or no.')
    return 'saveEmailAddresses'


def saveEmailAddresses(update: Update, context):
    user_input = update.message.text
    logger.debug(f'User Input:\n{user_input}')
    try:
        if user_input == 'yes':
            # for item in emailAddressList:
            for item in context.user_data['EmailList']:
                tmpResult = getDataFromDB(user=dbUsername,
                                          password=dbPass,
                                          host=dbHost,
                                          port=dbPort,
                                          database=dbConnectName,
                                          query=f"SELECT email FROM public.email_addresses WHERE email='{item}';")
                logger.debug(f'Result of SELECT query:\n{tmpResult}')

                if not tmpResult:
                    changeDataFromDB(user=dbUsername,
                                     password=dbPass,
                                     host=dbHost,
                                     port=dbPort,
                                     database=dbConnectName,
                                     query=f"INSERT INTO public.email_addresses(email) VALUES ('{item}');")
                    logger.info(f'Result of SELECT query:\n{tmpResult}')
                    update.message.reply_text(f'Email address {item} saved to database.')
                else:
                    update.message.reply_text(f'The email address {item} is already in the database. Not saved.')

        elif user_input == 'no':
            update.message.reply_text(
                f'The found email addresses are not saved in the database. Close the conversation.')
            logger.info(f'The found email addresses are not saved in the database')
            return ConversationHandler.END
        else:
            update.message.reply_text(f'Unexpected input. Close the conversation.')
            logger.info(f'Unexpected input. Close the conversation.')
            return ConversationHandler.END
    except Exception as e:
        logger.error(f'Error: {e}')
    return ConversationHandler.END


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Enter password to check complexity:')
    logger.info(f'Executed command /verify_password.')
    return 'verifyPassword'


def verifyPassword(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий пароль
    logger.debug(f'User input: {user_input}')
    passwordRegex = re.compile(r'(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*()])[0-9a-zA-Z!@#$%^&*]{8,}')
    checkPassword = passwordRegex.search(user_input)  # Проверяем пароль на соответствие регулярному выражению
    logger.debug(f'Value of checkPassword: {checkPassword}')

    if checkPassword:
        update.message.reply_text(f'Check results: password is complex.')
        logger.info(f'Check results: password is complex.')
    else:
        update.message.reply_text(f'Check results: password is simple.')
        logger.info(f'Check results: password is simple.')

    return ConversationHandler.END  # Завершаем работу обработчика диалога


def sshExecCommand(command, host, port, username, password):
    logging.info(f'Установка SSH подключения к удаленному серверу {sshHost}')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=username, password=password, port=port)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
    except Exception as e:
        logging.error(f'Connection error to remote server: {e}')
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    logging.info(f'Полученный результат: {data}')
    return data


def getRelease(update: Update, context):
    try:
        data = sshExecCommand(command='cat /etc/os-release',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информация о релизе:\n{data}')
    update.message.reply_text(f'Информация о релизе:\n{data}')
    return


def getUname(update: Update, context):
    try:
        data = sshExecCommand(command='uname -a',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информация об архитектуре процессора, имени хоста системы и версии ядра:\n{data}')
    update.message.reply_text(f'Информация об архитектуре процессора, имени хоста системы и версии ядра:\n{data}')
    return


def getUptime(update: Update, context):
    try:
        data = sshExecCommand(command='uptime',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информация о времени работы:\n{data}')
    update.message.reply_text(f'Информация о времени работы:\n{data}')
    return


def getDf(update: Update, context):
    try:
        data = sshExecCommand(command='df -h -x overlay -x tmpfs',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информации о состоянии файловой системы:\n{data}')
    update.message.reply_text(f'Информации о состоянии файловой системы:\n{data}')
    return


def getFree(update: Update, context):
    try:
        data = sshExecCommand(command='free -h',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информации о состоянии оперативной памяти:\n{data}')
    update.message.reply_text(f'Информации о состоянии оперативной памяти:\n{data}')
    return


def getMpstat(update: Update, context):
    try:
        data = sshExecCommand(command='mpstat -P ALL',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информации о производительности системы:\n{data}')
    update.message.reply_text(f'Информации о производительности системы:\n{data}')
    return


def getW(update: Update, context):
    try:
        data = sshExecCommand(command='w',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информации о работающих в данной системе пользователях:\n{data}')
    update.message.reply_text(f'Информации о работающих в данной системе пользователях:\n{data}')
    return


def getAuths(update: Update, context):
    try:
        data = sshExecCommand(command='last -n 10',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информации о последних 10 входах в систему:\n{data}')
    update.message.reply_text(f'Информации о последних 10 входах в систему:\n{data}')
    return


def getCritical(update: Update, context):
    try:
        data = sshExecCommand(command='sudo journalctl -p err -b -n 5 --no-pager',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    logger.debug(f'Информации о последних 5 критических событиях:\n{data}')
    update.message.reply_text(f'Информации о последних 5 критических событиях:\n{data}')
    return


def getPs(update: Update, context):
    try:
        data = sshExecCommand(command='ps -A',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    data = 'Информации о запущенных процессах:\n' + data
    logger.debug(f'{data}')
    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
        logger.debug(f'{data}')
    return


def getSs(update: Update, context):
    try:
        data = sshExecCommand(command='ss -tulpen',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')
    data = 'Информации об используемых портах:\n' + data
    logger.debug(f'{data}')
    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
        logger.debug(f'{data}')
    return


def getAptListCommand(update: Update, context):
    update.message.reply_text(
        'Для вывода информации о пакете введите его название или введите all для вывода информации обо всех пакетах')
    return 'getAptList'


def getAptList(update: Update, context):
    user_input = update.message.text
    try:
        if user_input == 'all':
            data = sshExecCommand(command='apt list --installed',
                                  host=sshHost,
                                  port=sshPort,
                                  username=sshUsername,
                                  password=sshPassword)
        else:
            data = sshExecCommand(command='apt list ' + user_input + ' --installed',
                                  host=sshHost,
                                  port=sshPort,
                                  username=sshUsername,
                                  password=sshPassword)
            if not user_input in data:
                data = 'Пакет не найден в системе'
    except Exception as e:
        logger.error(f'Error: {e}')
    data = f'Информации об установленных пакетах ({user_input}):\n' + data
    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
    return ConversationHandler.END


def getServices(update: Update, context):
    try:
        data = sshExecCommand(command='systemctl list-units --type=service',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')

    data = 'Информации о запущенных сервисах:\n' + data
    logger.debug(f'{data}')
    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
        logger.debug(f'{data}')
    return


def getReplLog(update: Update, context):
    try:
        data = sshExecCommand(command='sudo docker logs -n 100 $(sudo docker ps -q -f name=ptdevops-store-main) 2>&1 | grep -B1 -i replication',
                              host=sshHost,
                              port=sshPort,
                              username=sshUsername,
                              password=sshPassword)
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')

    data = 'Replication logs:\n' + data
    logger.debug(f'{data}')

    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
        logger.debug(f'textBlock = {textBlock}')
    return


def getEmailFromDB(update: Update, context):
    try:
        data = getDataFromDB(user=dbUsername,
                             password=dbPass,
                             host=dbHost,
                             port=dbPort,
                             database=dbConnectName,
                             query="SELECT email FROM public.email_addresses;")

    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')

    data = 'List of email addresses in the database:\n' + data
    logger.debug(f'{data}')

    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
        logger.debug(f'textBlock = {textBlock}')
    return


def getPhoneFromDB(update: Update, context):
    try:
        data = getDataFromDB(user=dbUsername,
                             password=dbPass,
                             host=dbHost,
                             port=dbPort,
                             database=dbConnectName,
                             query="SELECT number FROM public.phone_numbers;")
    except Exception as e:
        update.message.reply_text('Connection error to remote server.')
        logger.error('Connection error to remote server.')

    data = 'List of phone numbers in the database:\n' + data
    logger.debug(f'{data}')

    message = [data[i:i + 4096] for i in range(0, len(data), 4096)]
    for textBlock in message:
        update.message.reply_text(text=textBlock)
        logger.debug(f'textBlock = {textBlock}')
    return


def getDataFromDB(user, password, host, port, database, query):
    connection = None

    try:
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)

        cursor = connection.cursor()
        cursor.execute(query)
        rawData = cursor.fetchall()
        logger.debug(f"Raw SELECT data from database:\n{rawData}")

        dataLst = []
        for row in rawData:
            tmpLst = list(row)
            tmpStr = '. '.join(str(el) for el in tmpLst)
            dataLst.append(tmpStr)

        data = '\n'.join(str(el) for el in dataLst)
        logger.info(f"Result of SELECT query from database:\n{data}")
        logger.info("Command successfully executed")

    except (Exception, Error) as error:
        logger.error("Error working with PostgreSQL: %s", error)

    finally:
        if connection:
            cursor.close()
            connection.close()
            logger.info("Connection to PostgreSQL closed")
    return data


# Функция манипуляции с данными в БД (запросы INSERT, UPDATE, DELETE)
def changeDataFromDB(user, password, host, port, database, query):
    connection = None
    try:
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)

        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        logger.info("Command successfully executed")

    except (Exception, Error) as error:
        logger.error("Error working with PostgreSQL: %s", error)

    finally:
        if connection:
            cursor.close()
            connection.close()
            logger.info("Connection to PostgreSQL closed")
    return


def main():
    # Создайте программу обновлений и передайте ей токен вашего бота
    updater = Updater(token, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога поиска номеров телефонов
    convHandlerfindphonenumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findphonenumbersCommand)],
        states={
            'findphonenumbers': [MessageHandler(Filters.text & ~Filters.command, findphonenumbers)],
            'savePhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, savePhoneNumbers)],
        },
        fallbacks=[]
    )

    # Обработчик диалога поиска email адресов
    convHandlerFindEmailAddresses = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailAddressesCommand)],
        states={
            'findEmailAddresses': [MessageHandler(Filters.text & ~Filters.command, findEmailAddresses)],
            'saveEmailAddresses': [MessageHandler(Filters.text & ~Filters.command, saveEmailAddresses)],
        },
        fallbacks=[]
    )

    # Обработчик диалога проверки сложности пароля
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
    # Обработчик диалога cбора информации об установленных пакетах
    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'getAptList': [MessageHandler(Filters.text & ~Filters.command, getAptList)]
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpcommand))
    dp.add_handler(convHandlerfindphonenumbers)
    dp.add_handler(convHandlerFindEmailAddresses)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDf))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpstat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuths))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ps", getPs))
    dp.add_handler(CommandHandler("get_ss", getSs))
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(CommandHandler("get_services", getServices))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLog))
    dp.add_handler(CommandHandler("get_emails", getEmailFromDB))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhoneFromDB))

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
