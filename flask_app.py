from flask import Flask, request
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
sessionStorage = {}


@app.route("/post", methods=["POST"])
def main():
    data = request.json
    print(data)
    logging.info(f"Request: {data}")
    response = {
        "session": data["session"],
        "version": data["version"],
        "response": {
            "end_session": False
        }
    }
    start_dialog(data, response)
    logging.info(f"Response: {response}")

    return json.dumps(response)


def start_dialog(req, res):
    user_id = req["session"]["user_id"]
    if req["session"]["new"]:
        sessionStorage[user_id] = {
            "suggests": [
                "Нет",
                "Готов",
                "Конечно!"],
            "stage": 0,
            "inventory": [],
            "bugs": [0, 0, 0, 0],
            "level": 1
        }
        res["response"]["text"] = "Приветствую вас на новом рабочем месте!\nМы рады, что вы теперь у нас!" \
                                  "\nВаша задача - тестировать наши игры и отправлять баги, которые вы найдете в них." \
                                  "\nВаш первый рабочий день начинается." \
                                  " Для начала, мы хотим понять на что вы способны." \
                                  "\nПротестируйте один уровень из одной из наших старых игр." \
                                  " Там есть несколько багов.\n Чтобы работать у нас дальше, найдите их все.\n" \
                                  'Запрос со словом "баг" поможет узнать прогресс.' \
                                  "\nВы готовы?"
        res["response"]["buttons"] = get_suggests(user_id)
        return
    statements = ["на все сто", "да", "определенно", "готов", "конечно!"]
    if sessionStorage[user_id]["level"] == 2:
        second_level(res, req, user_id)
    elif req["request"]["original_utterance"].lower() in statements and sessionStorage[user_id]['stage'] == 0:
        res["response"]["card"] = {"type": "BigImage",
                                   "image_id": "965417/7072a36a16f5f8493dc3",
                                   "title": "Уровень 1",
                                   "description": "\nВы находитесь в небольшом городке на Диком Западе. "
                                                  "Рядом с вами ваша верная лошадь - Искра. Вы уже не довольны. "
                                                  "Вы бы назвали ее Плотвой.\n"
                                                  "Поехать на лошади из города или осмотреться?"}
        res["response"]["text"] = "\nВы находитесь в небольшом городке на Диком Западе. " \
                                  "Рядом с вами ваша верная лошадь - Искра." \
                                  " Вы уже не довольны." \
                                  " Вы бы назвали ее Плотвой.\nПоехать на лошади из города или осмотреться?"
        first_level(res, req, user_id)
    elif req["request"]["original_utterance"].lower() == 'нет' and sessionStorage[user_id]['stage'] == 0:
        res["response"]["text"] = "Тогда вам не место в нашей компании.\nИгра окончена."
        res["response"]["end_session"] = True
    elif 'баг' in req["request"]["original_utterance"].lower():
        res["response"]["text"] = "Баги: {}/4".format(sum(sessionStorage[user_id]["bugs"]))
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'осмотреться' and sessionStorage[user_id]['stage'] == 1:
        res["response"]["text"] = "Несколько зданий, кишащих людьми, пустующая палатка и небольшой костер рядом.\n" \
                                  "Избегая разговоров с людьми, вы заходите в первую палатку"
        first_tent(res, user_id)
    elif req["request"]["original_utterance"].lower() == 'открыть сундук' and sessionStorage[user_id]['stage'] == 2:
        res["response"]["text"] = "Вы взяли из сундука старый револьвер, несколько патронов и кошель," \
                                  " в котором лежит немного золота\n Вы вышли из палатки. Что дальше?"
        sessionStorage[user_id]["inventory"].extend(["револьвер", "кошель"])
        sessionStorage[user_id]["suggests"] = ["Подойти к костру", "Поехать на коне"]
        sessionStorage[user_id]["stage"] = 3
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'воровать плохо (выйти)' and \
            sessionStorage[user_id]['stage'] == 2:
        res["response"]["text"] = "Вы вышли из палатки. Что дальше?"
        sessionStorage[user_id]["suggests"] = ["Подойти к костру", "Поехать на коне"]
        sessionStorage[user_id]["stage"] = 3
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'подойти к костру' and sessionStorage[user_id]['stage'] == 3:
        res["response"]["text"] = "Рядом с костром на доске лежит кусок сырого мяса." \
                                  " Человек, который принес мясо только что куда-то ушел."
        sessionStorage[user_id]["suggests"] = ["Пожарить мясо", "Поехать на коне"]
        sessionStorage[user_id]["stage"] = 4
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'пожарить мясо' and sessionStorage[user_id]['stage'] == 4:
        res["response"]["text"] = "Пока вы жарили мясо, на вас напали все жители города." \
                                  " Непонятно почему. Как только вы начинаете отбиваться," \
                                  " вас телепортирует в текстуры. Кажется, вы нашли баг."
        sessionStorage[user_id]["bugs"][0] = 1
        first_level_restarted(res, req, user_id)
    elif 'поехать' in req["request"]["original_utterance"].lower() and sessionStorage[user_id]["stage"] in [1, 2, 3, 4]:
        res["response"]["text"] = "Вы едете по полю. Вокруг ни души." \
                                  " Вдруг вы видите повозку с припасами, у которой сломалось колесо"
        sessionStorage[user_id]["suggests"] = ["Помочь кучеру", "Ограбить кучера"]
        sessionStorage[user_id]["stage"] = 5
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'помочь кучеру' and sessionStorage[user_id]['stage'] == 5:
        res["response"]["text"] = "Вы помогли кучеру починить колесо." \
                                  " За это он дает вам круг сыра и немного моркови для вашей лошади"
        sessionStorage[user_id]["suggests"] = ["Покормить Искру морковью", "Поехать дальше"]
        sessionStorage[user_id]["stage"] = 6
        sessionStorage[user_id]["inventory"].append("сыр")
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'ограбить кучера' and sessionStorage[user_id]['stage'] == 5:
        if 'револьвер' not in sessionStorage[user_id]["inventory"]:
            res["response"]["text"] = "Вы сказали кучеру, что теперь эта повозка принадлежит вам." \
                                      " Он посмеялся и застрелил вас. \nКакой-то агрессивный кучер"
            first_level_restarted(res, req, user_id, bug=False)
        else:
            res["response"]["text"] = "Угрожая пистолетом кучеру, вы говорите, что теперь эта повозка принадлежит вам" \
                                      "Кучер молит о пощаде"
            sessionStorage[user_id]["suggests"] = ["Пощадить", "Застрелить"]
            sessionStorage[user_id]["stage"] = 9
            res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'пощадить' and sessionStorage[user_id]['stage'] == 9:
        res["response"]["text"] = "Вы отпускаете кучера и начинаете осматривать содержимое повозки." \
                                  " Вдруг вы слышите какие-то звуки позади себя. Обернувшись," \
                                  " вы видите кучера, который направил на вас револьвер. Выстрел. Вы мертвы.\n" \
                                  "Ожидаемо, если честно"
        first_level_restarted(res, req, user_id, bug=False)
    elif req["request"]["original_utterance"].lower() == 'застрелить' and sessionStorage[user_id]['stage'] == 9:
        res["response"]["text"] = "Застрелив бедного кучера, вы начинаете осматривать повозку." \
                                  " Вы находите много моркови, которой кормите Искру. Себе берете круг сыра и топор"
        sessionStorage[user_id]["suggests"] = ['Поехать дальше']
        sessionStorage[user_id]["stage"] = 10
        sessionStorage[user_id]["inventory"].append("сыр")
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'покормить искру морковью' \
            and sessionStorage[user_id]['stage'] == 6:
        res["response"]["text"] = "Вы скормили лошади всю морковь, но она явно все еще хочет есть"
        sessionStorage[user_id]["suggests"] = ["Поехать дальше", "Скормить сыр"]
        if 'револьвер' in sessionStorage[user_id]["inventory"]:
            sessionStorage[user_id]["suggests"].append("Скормить револьвер лошади")
        sessionStorage[user_id]["stage"] = 7
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'скормить револьвер лошади' \
            and sessionStorage[user_id]['stage'] == 7 and 'револьвер' in sessionStorage[user_id]["inventory"]:
        res["response"]["text"] = "Игра пришла в замешательство от такого глупого действия и вылетела"
        sessionStorage[user_id]["bugs"][1] = 1
        first_level_restarted(res, req, user_id)
    elif req["request"]["original_utterance"].lower() == 'скормить сыр' and sessionStorage[user_id]['stage'] == 7:
        res["response"]["text"] = "Теперь лошадь сыта"
        sessionStorage[user_id]["suggests"] = ["Поехать дальше"]
        sessionStorage[user_id]["stage"] = 8
        sessionStorage[user_id]["inventory"].remove("сыр")
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'поехать дальше' and \
            sessionStorage[user_id]['stage'] in [6, 7, 8, 10]:
        res["response"]["text"] = "Вы довольно долго скачете на лошади. По сторонам совершенно ничего нет." \
                                  " Вдруг вы видите кирпичную стену справа от вас"
        sessionStorage[user_id]["suggests"] = ["Это же стена посреди поля!", "Не обращать внимания"]
        sessionStorage[user_id]["stage"] = 11
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'это же стена посреди поля!' \
            and sessionStorage[user_id]['stage'] == 11:
        res["response"]["text"] = "Стена посреди поля - это очень странно, поэтому вы думаете," \
                                  " что стену добавили специально,чтобы понять на что вы способны." \
                                  "Скорее всего, через нее можно пройти"
        sessionStorage[user_id]["suggests"] = ["Будем тестить", "Попытки того не стоят (уйти)"]
        sessionStorage[user_id]["stage"] = 12
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'будем тестить' and sessionStorage[user_id]['stage'] == 12:
        res["response"]["text"] = "Вы вот уже целых 2 часа пытаетесь пройти через эту стену," \
                                  " но видимо Добби закрыл проход. "
        if 'сыр' not in sessionStorage[user_id]["inventory"]:
            res["response"]["text"] += "\nВы понимаете, что в данной ситуации невозможно пройти сквозь стену." \
                                       " Нужно попытаться найти больше предметов"
            sessionStorage[user_id]["suggests"] = ["Отправиться дальше"]
            sessionStorage[user_id]["stage"] = 13
            res["response"]["buttons"] = get_suggests(user_id)
        else:
            res["response"]["text"] += "Вдруг вам в голову приходит гениальная идея. " \
                                       "Вы встаете на круг сыра, разворачиваетесь спиной к стене," \
                                       " приседаете, и одновременно с этим меняете оружие в руках. Получилось!" \
                                       " Вас протолкунуло в стену."
            sessionStorage[user_id]["bugs"][2] = 1
            first_level_restarted(res, req, user_id)
    elif (req["request"]["original_utterance"].lower() == 'не обращать внимания' and
          sessionStorage[user_id]['stage'] == 11) or \
            (req["request"]["original_utterance"].lower() == 'отправиться дальше' and
             sessionStorage[user_id]['stage'] == 13) or \
            (req["request"]["original_utterance"].lower() == 'попытки того не стоят (уйти)' and
             sessionStorage[user_id]['stage'] == 12):
        res["response"]["text"] = "Вы продолжаете ехать на коне и вдруг провалились в текстуры. Эм, ну, вы нашли баг."
        sessionStorage[user_id]["bugs"][3] = 1
        first_level_restarted(res, req, user_id)
    else:
        res["response"]["text"] = "Пожалуйста, выражайтесь яснее"
        res["response"]["buttons"] = get_suggests(user_id)
        return


def second_level(res, req, user_id):
    if sessionStorage[user_id]["stage"] == 0:
        res["response"]["card"] = {"type": "BigImage",
                                   "image_id": "1652229/f9fa7b4bccdfadb12070",
                                   "title": "Уровень 2",
                                   "description": "В игре вы управляете одной криминальной семьей в Британии."
                                                  " Под вашим влиянием часть небольшого города."
                                                  " Ваш бар поздно ночью подорвали. У вас есть предположение, что это"
                                                  " сделала итальянская мафия или же американцы."
                                                  " На кого напасть?"}
        res["response"]["text"] = " В игре вы управляете одной криминальной семьей в Британии." \
                                  " Под вашим влиянием часть небольшого города." \
                                  " Ваш бар поздно ночью подорвали. У вас есть предположение, что это" \
                                  " сделала итальянская мафия, с которой вы враждуете," \
                                  " или же американцы, с которыми вы порвали все деловые отношения." \
                                  " У двери вы нашли пулю с вырезанным на ней вашем именем." \
                                  " На кого напасть?"
        sessionStorage[user_id]["suggests"] = ["Американцы", "Итальянцы"]
        sessionStorage[user_id]["stage"] = 1
        res["response"]["buttons"] = get_suggests(user_id)
    elif 'баг' in req["request"]["original_utterance"].lower():
        res["response"]["text"] = "Баги: {}/2".format(sum(sessionStorage[user_id]["bugs"]))
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'итальянцы' and sessionStorage[user_id]['stage'] == 1:
        res["response"]["text"] = "В 6 часов ваша семья напала на территории итальянцев." \
                                  " Ваши люди грабят, убивают их, пьют и вспоминают войну." \
                                  " Многие ваши погибли, но вы победили. Босс итальянской семьи был взят здесь же." \
                                  " Он говорит, что это они напали на вас. Узнав от него достаточно информации, " \
                                  "вы убиваете его и уходите."
        sessionStorage[user_id]["suggests"] = ["Вернуться и попытаться найти ошибки", "Окончательно уйти"]
        sessionStorage[user_id]["stage"] = 2
        res["response"]["buttons"] = get_suggests(user_id)
    elif 'вернуться' in req["request"]["original_utterance"].lower() and sessionStorage[user_id]['stage'] == 2:
        res["response"]["text"] = "Когда вы возвращаетесь обратно, то не находите ни следов битвы, ни трупов," \
                                  " никаких следов. Хотя это было 5 минут назад по игровому времени." \
                                  "Других проблем не нашлось.\n"
        sessionStorage[user_id]["bugs"][0] = 1
        second_level_restarted(res, user_id)
    elif 'уйти' in req["request"]["original_utterance"].lower() and sessionStorage[user_id]['stage'] == 2:
        res["response"]["text"] = "Теперь вы полностью контролируете незаконную торговлю табаком." \
                                  " Деньги текут рекой, в семье появляются новые люди, и вы понимаете," \
                                  " что теперь вы сможете уничтожить американцев и" \
                                  " полностью контролировать город."
        sessionStorage[user_id]["suggests"] = ["Начать войну", "Заключить сделку с американцами"]
        sessionStorage[user_id]["stage"] = 3
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'заключить сделку с американцами' and \
            sessionStorage[user_id]['stage'] == 3:
        res["response"]["text"] = "Понимая свое положение, американская семья заключает сделку на ваших условиях." \
                                  " Она остаются существовать и может продолжать незаконную торговлю," \
                                  " но должна подчинятся вашим приказам. От одного из американцев" \
                                  " вы узнаете о возможности обосноваться в Лондоне." \
                                  " На этом ваша часть игры, предназначенная для тестов, заканчивается"
        second_level_restarted(res, user_id, bug=False)
    elif (req["request"]["original_utterance"].lower() == 'американцы' and sessionStorage[user_id]['stage'] == 1) \
            or ('начать' in req["request"]["original_utterance"].lower() and sessionStorage[user_id]['stage'] == 3):
        res["response"]["text"] = "Вы решаете напасть на дворец американской семьи." \
                                  " Начать аккуратую тактику или пойти в бой в самое пекло?"
        sessionStorage[user_id]["suggests"] = ["Аккуратно", "В самое пекло"]
        sessionStorage[user_id]["stage"] = 4
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'в самое пекло' and sessionStorage[user_id]['stage'] == 4:
        res["response"]["text"] = "Ваша армия привыкла к войне. Многие погибли, ваш брат получил тяжелое ранение," \
                                  " но вы победили, все территории теперь ваши. Далее ваша отрезок игры заканчивается"
        second_level_restarted(res, user_id, bug=False)
    elif req["request"]["original_utterance"].lower() == 'аккуратно' and sessionStorage[user_id]['stage'] == 4:
        res["response"]["text"] = "Ваши люди обходят американцев, после взятия в кольцо, они пошли в бой. " \
                                  "Несколько людей сидят с винтовками на холмах. Вы потеряли много людей," \
                                  " победили и расширили сферы влияния, но глава мафии с небольшой группой" \
                                  " взял в плен вашего брата. Договориться или пойти в бой с ними?"
        sessionStorage[user_id]["suggests"] = ["Договориться", "В бой"]
        sessionStorage[user_id]["stage"] = 5
        res["response"]["buttons"] = get_suggests(user_id)
    elif req["request"]["original_utterance"].lower() == 'договориться' and sessionStorage[user_id]['stage'] == 5:
        res["response"]["text"] = "К американцам вернулась часть их территорий, а также денег." \
                                  " Вы получили брата назад. На этом ваша часть игры," \
                                  " предназначенная для тестов, заканчивается"
        second_level_restarted(res, user_id, bug=False)
    elif req["request"]["original_utterance"].lower() == 'в бой' and sessionStorage[user_id]['stage'] == 5:
        res["response"]["text"] = "Вы напали, и они выстрелили в брата. Он погиб. " \
                                  "Вы перебили всех. Но в субтитрах последней фразы босса американцев," \
                                  " вы нашли грамматическую ошибку. Запишем в баги"
        sessionStorage[user_id]["bugs"][1] = 1
        second_level_restarted(res, user_id, bug=False)
    else:
        res["response"]["text"] = "Пожалуйста, выражайтесь яснее"
        res["response"]["buttons"] = get_suggests(user_id)
        return


def second_level_restarted(res, user_id, bug=True):
    if sum(sessionStorage[user_id]["bugs"]) != 2:
        if bug:
            res["response"]["text"] += "\n\nВы описываете данную проблему и начинаете игру заново\n\n"
        else:
            res["response"]["text"] += "\n\nНе найдя ничего интересного, вы начинаете проходить уровень заново.\n\n"
        res["response"]["text"] += " В игре вы управляете одной криминальной семьей в Британии." \
                                   " Под вашим влиянием часть небольшого города." \
                                   " Ваш бар поздно ночью подорвали. У вас есть предположение, что это" \
                                   " сделала итальянская мафия, с которой вы враждуете, у которой вы" \
                                   " забрали их территорию и убили одного из членов мафии неделю назад," \
                                   " или же американцы, с которыми вы порвали все деловые отношения." \
                                   " У двери вы нашли пулю с вырезанным на ней вашем именем." \
                                   " На кого напасть?"
        sessionStorage[user_id]["suggests"] = ["Итальянцы", "Американцы"]
        sessionStorage[user_id]["stage"] = 1
        sessionStorage[user_id]["inventory"] = []
        res["response"]["buttons"] = get_suggests(user_id)
    else:
        res["response"]["text"] = "После окончания рабочего дня компания разочарована в вас," \
                                  " потому что другой работник, тестирующий тот же самый момент игры," \
                                  " нашел один очень труднореализуемый баг, который не смогли найти вы." \
                                  "Вы были уволены. Но вам не привыкать - такова жизнь тестера. Игра окончена"
        res["response"]["end_session"] = True


def first_level_restarted(res, req, user_id, bug=True):
    if sum(sessionStorage[user_id]["bugs"]) != 4:
        if bug:
            res["response"]["text"] += "\n\nВы документируете найденный баг и начинаете игру заново"
        else:
            res["response"]["text"] += "\n\nНе найдя багов, вы начинаете проходить уровень заново"
        res["response"]["text"] += "\n\nВы находитесь в небольшом городке на Диком Западе. " \
                                   "Рядом с вами ваша верная лошадь - Искра. " \
                                   "\nПоехать на лошади из города или осмотреться?"
    first_level(res, req, user_id)


def first_level(res, req, user_id):
    sessionStorage[user_id]["suggests"] = ["Поехать", "Осмотреться"]
    sessionStorage[user_id]["stage"] = 1
    sessionStorage[user_id]["inventory"] = []
    if sum(sessionStorage[user_id]["bugs"]) == 4:
        sessionStorage[user_id]["stage"] = 0
        sessionStorage[user_id]["bugs"] = [0, 0]
        sessionStorage[user_id]["level"] = 2
        second_level(res, req, user_id)
    else:
        res["response"]["buttons"] = get_suggests(user_id)


def first_tent(res, user_id):
    sessionStorage[user_id]["suggests"] = ["Открыть сундук", "Воровать плохо (выйти)"]
    sessionStorage[user_id]['stage'] = 2
    res["response"]["buttons"] = get_suggests(user_id)


def get_suggests(user_id):
    session = sessionStorage[user_id]
    suggests = [
        {"title": suggest, "hide": True}
        for suggest in session["suggests"]
    ]
    return suggests


if __name__ == '__main__':
    app.run(port=8080, host="127.0.0.1")
