# encoding=utf-8

"""

@file: question_temp.py

@time: 2020/03/29

@desc:
设置问题模板，为每个模板设置对应的SPARQL语句。demo提供如下模板：

1. 如何制作某道菜品？
2. 某道菜品需要哪些原料？
3. 某个食品大类包含哪些具体菜品？
4. 某个菜品的主料是什么？
5. 某个菜品的特色是什么？
6. 某个菜品的制作步骤是什么？

读者可以自己定义其他的匹配规则。
"""
from refo import finditer, Predicate, Star, Any, Disjunction
import re

# TODO SPARQL前缀和模板
SPARQL_PREXIX = u"""
PREFIX : <http://kg.course/ai-food-time/>
"""

SPARQL_SELECT_TEM = u"{prefix}\n" + \
    u"SELECT DISTINCT {select} WHERE {{\n" + \
    u"{expression}\n" + \
    u"}}\n"

SPARQL_COUNT_TEM = u"{prefix}\n" + \
    u"SELECT COUNT({select}) WHERE {{\n" + \
    u"{expression}\n" + \
    u"}}\n"

SPARQL_ASK_TEM = u"{prefix}\n" + \
    u"ASK {{\n" + \
    u"{expression}\n" + \
    u"}}\n"

INDENT = "    "


class W(Predicate):
    def __init__(self, token=".*", pos=".*"):
        self.token = re.compile(token + "$")
        self.pos = re.compile(pos + "$")
        super(W, self).__init__(self.match)

    def match(self, word):
        m1 = self.token.match(word.token)
        m2 = self.pos.match(word.pos)
        return m1 and m2


class Rule(object):
    def __init__(self, condition_num, condition=None, action=None):
        assert condition and action
        self.condition = condition
        self.action = action
        self.condition_num = condition_num

    def apply(self, sentence):
        matches = []
        for m in finditer(self.condition, sentence):
            i, j = m.span()
            matches.extend(sentence[i:j])

        return self.action(matches), self.condition_num


class KeywordRule(object):
    def __init__(self, condition=None, action=None):
        assert condition and action
        self.condition = condition
        self.action = action

    def apply(self, sentence):
        matches = []
        for m in finditer(self.condition, sentence):
            i, j = m.span()
            matches.extend(sentence[i:j])
        if len(matches) == 0:
            return None
        else:
            return self.action()


class QuestionSet:
    def __init__(self):
        pass

    @staticmethod
    def has_movie_question(word_objects):
        """
        某演员演了什么电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?m." \
                    u"?m :movieTitle ?x".format(person=w.token)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break
        return sparql

    @staticmethod
    def has_actor_question(word_objects):
        """
        哪些演员参演了某电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            if w.pos == pos_movie:
                e = u"?m :movieTitle '{movie}'." \
                    u"?m :hasActor ?a." \
                    u"?a :personName ?x".format(movie=w.token)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break

        return sparql

    @staticmethod
    def has_cooperation_question(word_objects):
        """
        演员A和演员B有哪些合作的电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        person1 = None
        person2 = None

        for w in word_objects:
            if w.pos == pos_person:
                if person1 is None:
                    person1 = w.token
                else:
                    person2 = w.token
        if person1 is not None and person2 is not None:
            e = u"?p1 :personName '{person1}'." \
                u"?p2 :personName '{person2}'." \
                u"?p1 :hasActedIn ?m." \
                u"?p2 :hasActedIn ?m." \
                u"?m :movieTitle ?x".format(person1=person1, person2=person2)

            return SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                            select=select,
                                            expression=e)
        else:
            return None

    @staticmethod
    def has_compare_question(word_objects):
        """
        某演员参演的评分高于X的电影有哪些？
        :param word_objects:
        :return:
        """
        select = u"?x"

        person = None
        number = None
        keyword = None

        for r in compare_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        for w in word_objects:
            if w.pos == pos_person:
                person = w.token

            if w.pos == pos_number:
                number = w.token

        if person is not None and number is not None:

            e = u"?p :personName '{person}'." \
                u"?p :hasActedIn ?m." \
                u"?m :movieTitle ?x." \
                u"?m :movieRating ?r." \
                u"filter(?r {mark} {number})".format(person=person, number=number,
                                                     mark=keyword)

            return SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                            select=select,
                                            expression=e)
        else:
            return None

    @staticmethod
    def has_movie_type_question(word_objects):
        """
        某演员演了哪些类型的电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?m." \
                    u"?m :hasGenre ?g." \
                    u"?g :genreName ?x".format(person=w.token)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break
        return sparql

    @staticmethod
    def has_specific_type_movie_question(word_objects):
        """
        某演员演了什么类型（指定类型，喜剧、恐怖等）的电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        keyword = None
        for r in genre_keyword_rules:
            keyword = r.apply(word_objects)

            if keyword is not None:
                break

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?m." \
                    u"?m :hasGenre ?g." \
                    u"?g :genreName '{keyword}'." \
                    u"?m :movieTitle ?x".format(
                        person=w.token, keyword=keyword)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break
        return sparql

    @staticmethod
    def has_quantity_question(word_objects):
        """
        某演员演了多少部电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?x.".format(person=w.token)

                sparql = SPARQL_COUNT_TEM.format(
                    prefix=SPARQL_PREXIX, select=select, expression=e)
                break

        return sparql

    @staticmethod
    def is_comedian_question(word_objects):
        """
        某演员是喜剧演员吗
        :param word_objects:
        :return:
        """
        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s rdf:type :Comedian.".format(person=w.token)

                sparql = SPARQL_ASK_TEM.format(
                    prefix=SPARQL_PREXIX, expression=e)
                break

        return sparql

    @staticmethod
    def has_basic_person_info_question(word_objects):
        """
        某演员的基本信息是什么
        :param word_objects:
        :return:
        """

        keyword = None
        for r in person_basic_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        select = u"?x"
        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                if isinstance(keyword, str):
                    e = u"{indent}?s :中文名 ?o. \n" \
                        u"{indent}?s {keyword} ?x. \n" \
                        u"{indent}FILTER REGEX(STR(?o), '{person}').".format(person=w.token, keyword=keyword, indent=INDENT)
                elif isinstance(keyword, list):
                    e = u"{indent}?s :中文名 ?o. \n".format(indent=INDENT)
                    for k in keyword:
                        e += u"{indent}OPTIONAL {{?s {keyword} ?x.}} \n".format(keyword=k, indent=INDENT)
                    e += u"{indent}FILTER REGEX(STR(?o), '{person}').".format(person=w.token, indent=INDENT)

                sparql = SPARQL_SELECT_TEM.format(
                    prefix=SPARQL_PREXIX, select=select, expression=e)

                break

        return sparql

    @staticmethod
    def has_basic_movie_info_question(word_objects):
        """
        某电影的基本信息是什么
        :param word_objects:
        :return:
        """

        keyword = None
        for r in movie_basic_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        select = u"?x"
        sparql = None
        for w in word_objects:
            if w.pos == pos_movie:
                e = u"?s :movieTitle '{movie}'." \
                    u"?s {keyword} ?x.".format(movie=w.token, keyword=keyword)

                sparql = SPARQL_SELECT_TEM.format(
                    prefix=SPARQL_PREXIX, select=select, expression=e)

                break

        return sparql

    @staticmethod
    def has_basic_food_info_question(word_objects):
        """
        某电影的基本信息是什么
        :param word_objects:
        :return:
        """

        keyword = None
        for r in food_basic_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        select = u"?x"
        sparql = None
        for w in word_objects:
            if w.pos == pos_food:
                e = u"?s :名称 '{food}'. \n" \
                    u"?s {keyword} ?x.".format(food=w.token, keyword=keyword)

                sparql = SPARQL_SELECT_TEM.format(
                    prefix=SPARQL_PREXIX, select=select, expression=e)

                break

        return sparql

    @staticmethod
    def who_born_in_question(word_objects):
        """
        谁出生在xx/出生在xxx的有谁
        :param word_objects:
        :return:
        """
        keyword = PropertyValueSet.return_birth_place_value()

        select = u"?x"
        sparql = None
        for w in word_objects:
            if w.pos == pos_place:
                if isinstance(keyword, str):
                    e = u"{indent}?s :中文名 ?x. \n" \
                        u"{indent}?s {keyword} ?o. \n" \
                        u"{indent}FILTER REGEX(STR(?o), '{place}').".format(place=w.token, keyword=keyword, indent=INDENT)
                elif isinstance(keyword, list):
                    e = u"{indent}?s :中文名 ?x. \n".format(indent=INDENT)
                    for k in keyword:
                        e += u"{indent}OPTIONAL {{?s {keyword} ?o.}} \n".format(keyword=k, indent=INDENT)
                    e += u"{indent}FILTER REGEX(STR(?o), '{place}').".format(place=w.token, indent=INDENT)
                else:
                    print('[Error]: the type(keyword) should be either `str` or list, but now is {}'.format(type(keyword)))

                sparql = SPARQL_SELECT_TEM.format(
                    prefix=SPARQL_PREXIX, select=select, expression=e)

                break

        return sparql


class PropertyValueSet:
    def __init__(self):
        pass

    @staticmethod
    def return_adventure_value():
        return u'冒险'

    @staticmethod
    def return_fantasy_value():
        return u'奇幻'

    @staticmethod
    def return_animation_value():
        return u'动画'

    @staticmethod
    def return_drama_value():
        return u'剧情'

    @staticmethod
    def return_thriller_value():
        return u'恐怖'

    @staticmethod
    def return_action_value():
        return u'动作'

    @staticmethod
    def return_comedy_value():
        return u'喜剧'

    @staticmethod
    def return_history_value():
        return u'历史'

    @staticmethod
    def return_western_value():
        return u'西部'

    @staticmethod
    def return_horror_value():
        return u'惊悚'

    @staticmethod
    def return_crime_value():
        return u'犯罪'

    @staticmethod
    def return_documentary_value():
        return u'纪录'

    @staticmethod
    def return_fiction_value():
        return u'科幻'

    @staticmethod
    def return_mystery_value():
        return u'悬疑'

    @staticmethod
    def return_music_value():
        return u'音乐'

    @staticmethod
    def return_romance_value():
        return u'爱情'

    @staticmethod
    def return_family_value():
        return u'家庭'

    @staticmethod
    def return_war_value():
        return u'战争'

    @staticmethod
    def return_tv_value():
        return u'电视电影'

    @staticmethod
    def return_higher_value():
        return u'>'

    @staticmethod
    def return_lower_value():
        return u'<'

    @staticmethod
    def return_birth_value():
        return u':生日'

    @staticmethod
    def return_birth_place_value():
        return list([u':出生地', u':出身', u':出身地'])

    @staticmethod
    def return_english_name_value():
        return u':外文名'

    @staticmethod
    def return_person_introduction_value():
        return u':personBiography'

    # ------
    # vivire card additional person basic
    @staticmethod
    def return_blood_type_value():
        return u':血型'

    @staticmethod
    def return_zodiac_sign_value():
        return u':星座'

    @staticmethod
    def return_haki_type_value():
        return u':霸气'

    @staticmethod
    def return_height_value():
        return list([u':身高', u':全长', u':全高', u':身长', u':高度'])
    # ------

    @staticmethod
    def return_movie_introduction_value():
        return u':movieIntroduction'

    @staticmethod
    def return_release_value():
        return u':movieReleaseDate'

    @staticmethod
    def return_rating_value():
        return u':movieRating'

    @staticmethod
    def return_subtype_value():
        return u':属于'

    @staticmethod
    def return_material_value():
        return u':选材'

    @staticmethod
    def return_main_value():
        return u':主料'

    @staticmethod
    def return_excipient_value():
        return u':辅料'

    @staticmethod
    def return_ingredient_value():
        return u':配料'

    @staticmethod
    def return_makesteps_value():
        return u':制作步骤'

    @staticmethod
    def return_features_value():
        return u':特色'


# TODO 定义关键词
pos_person = "nr"
pos_movie = "nz"
pos_number = "m"
pos_place = "ns"
pos_food = "ai"

person_entity = (W(pos=pos_person))
movie_entity = (W(pos=pos_movie))
number_entity = (W(pos=pos_number))
place_entity = (W(pos=pos_place))
food_entity = (W(pos=pos_food))

adventure = W("冒险")
fantasy = W("奇幻")
animation = (W("动画") | W("动画片"))
drama = (W("剧情") | W("剧情片"))
thriller = (W("恐怖") | W("恐怖片"))
action = (W("动作") | W("动作片"))
comedy = (W("喜剧") | W("喜剧片"))
history = (W("历史") | W("历史剧"))
western = (W("西部") | W("西部片"))
horror = (W("惊悚") | W("惊悚片"))
crime = (W("犯罪") | W("犯罪片"))
documentary = (W("纪录") | W("纪录片"))
science_fiction = (W("科幻") | W("科幻片"))
mystery = (W("悬疑") | W("悬疑片"))
music = (W("音乐") | W("音乐片"))
romance = (W("爱情") | W("爱情片"))
family = W("家庭")
war = (W("战争") | W("战争片"))
TV = W("电视")
genre = (adventure | fantasy | animation | drama | thriller | action
         | comedy | history | western | horror | crime | documentary |
         science_fiction | mystery | music | romance | family | war
         | TV)


actor = (W("演员") | W("艺人") | W("表演者"))
movie = (W("电影") | W("影片") | W("片子") | W("片") | W("剧"))
category = (W("类型") | W("种类"))
several = (W("多少") | W("几部"))

higher = (W("大于") | W("高于"))
lower = (W("小于") | W("低于"))
compare = (higher | lower)

# original
birth = (W("生日") | W("出生") + W("日期") | W("出生"))
birth_place = (W("出生地") | W("出生"))
english_name = (W("英文名") | W("英文") + W("名字") | W("外文") + W("名") | W("外文") + W("名字"))
introduction = (W("介绍") | W("是") + W("谁") | W("简介"))
# ------
# vivire card additional person basic
blood_type = W("血型")
zodiac_sign = W("星座")
haki_type = W("霸气")
height = (W("身高") | W("身长") | W("高度") | W("长度") | W("全长") | W("全高"))
# ------
person_basic = (birth | birth_place | english_name | introduction | blood_type | zodiac_sign | haki_type | height)

rating = (W("评分") | W("分") | W("分数"))
release = (W("上映"))
movie_basic = (rating | introduction | release)

when = (W("何时") | W("时候"))
where = (W("哪里") | W("哪儿") | W("何地") | W("何处") | W("在") + W("哪"))
who = W("谁")

# ai-food-time
makestep = (W("制作") + W("步骤") | W("做法") | W("烹饪") + W("方法") | W("制作") + W("方法") | W("制作"))
subtype = (W("包括") | W("子菜品") | W("分为") | W("包含"))
material = (W("取材") | W("原料") | W("用到") | W("选材") | W("食材"))
main_component = (W("主料") | W("主要原料"))
excipient = (W("辅料"))
ingredient = (W("配料"))
feature = (W("特色") | W("特点"))
what = (W("哪些") | W("什么"))
how = (W("怎样") | W("如何"))
make = W("制作")

food_basic = (makestep | subtype | material | main_component | excipient | ingredient | feature)

# TODO 问题模板/匹配规则
"""
1. 某演员演了什么电影
2. 某电影有哪些演员出演
3. 演员A和演员B合作出演了哪些电影
4. 某演员参演的评分大于X的电影有哪些
5. 某演员出演过哪些类型的电影
6. 某演员出演的XX类型电影有哪些。
7. 某演员出演了多少部电影。
8. 某演员是喜剧演员吗。
9. 某人的生日/出生地/英文名/简介/血型/星座/霸气/身高
10. 某电影的简介/上映日期/评分
11. 谁出生在xx/出生在xxx的有谁
"""
rules = [
    Rule(condition_num=2, condition=person_entity + Star(Any(), greedy=False) +
         movie + Star(Any(), greedy=False), action=QuestionSet.has_movie_question),
    Rule(condition_num=2, condition=(movie_entity + Star(Any(), greedy=False) + actor + Star(Any(), greedy=False)) |
         (actor + Star(Any(), greedy=False) + movie_entity + Star(Any(), greedy=False)), action=QuestionSet.has_actor_question),
    Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + person_entity + Star(Any(),
                                                                                                     greedy=False) + (movie | Star(Any(), greedy=False)), action=QuestionSet.has_cooperation_question),
    Rule(condition_num=4, condition=person_entity + Star(Any(), greedy=False) + compare + number_entity +
         Star(Any(), greedy=False) + movie + Star(Any(), greedy=False), action=QuestionSet.has_compare_question),
    Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + category +
         Star(Any(), greedy=False) + movie, action=QuestionSet.has_movie_type_question),
    Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + genre + Star(Any(),
                                                                                             greedy=False) + (movie | Star(Any(), greedy=False)), action=QuestionSet.has_specific_type_movie_question),
    Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + several + Star(Any(),
                                                                                               greedy=False) + (movie | Star(Any(), greedy=False)), action=QuestionSet.has_quantity_question),
    Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + comedy +
         actor + Star(Any(), greedy=False), action=QuestionSet.is_comedian_question),
    Rule(condition_num=3, condition=(person_entity + Star(Any(), greedy=False) + (when | where) + person_basic + Star(Any(), greedy=False)) |
         (person_entity + Star(Any(), greedy=False) + person_basic + Star(Any(), greedy=False)), action=QuestionSet.has_basic_person_info_question),
    Rule(condition_num=2, condition=movie_entity + Star(Any(), greedy=False) + movie_basic +
         Star(Any(), greedy=False), action=QuestionSet.has_basic_movie_info_question),
    Rule(condition_num=3, condition=(who + Star(Any(), greedy=False) + birth_place + Star(Any(), greedy=False) + place_entity + Star(Any(), greedy=False)) |
         (birth_place + Star(Any(), greedy=False) + place_entity + Star(Any(), greedy=False) + who), action=QuestionSet.who_born_in_question),
    #Rule(condition_num=2, condition=(what + Star(Any(), greedy=False) + food_entity + Star(Any(), greedy=False) + food_basic + Star(Any(), greedy=False)) |
    #     (food_entity + Star(Any(), greedy=False) + food_basic + Star(Any(), greedy=False)), action=QuestionSet.has_basic_food_info_question),
    Rule(condition_num=2, condition=(food_entity + Star(Any(), greedy=False) + food_basic + Star(Any(), greedy=False)) | (Star(Any(), greedy=False) + make + Star(Any(), greedy=False) + food_entity + Star(Any(), greedy=False)), action=QuestionSet.has_basic_food_info_question),
]

# TODO 具体的属性词匹配规则
genre_keyword_rules = [
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + adventure + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_adventure_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + fantasy + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_fantasy_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + animation + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_animation_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + drama + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_drama_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + thriller + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_thriller_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + action + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_action_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + comedy + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_comedy_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + history + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_history_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + western + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_western_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + horror + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_horror_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + crime + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_crime_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + documentary + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_documentary_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + science_fiction + Star(Any(),
                                                                                             greedy=False) + (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_fiction_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + mystery + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_mystery_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + music + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_music_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + romance + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_romance_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + family + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_family_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + war + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_war_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + TV + Star(Any(), greedy=False) +
                (movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_tv_value)
]

compare_keyword_rules = [
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + higher + number_entity + Star(Any(),
                                                                                                    greedy=False) + movie + Star(Any(), greedy=False), action=PropertyValueSet.return_higher_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + lower + number_entity + Star(Any(),
                                                                                                   greedy=False) + movie + Star(Any(), greedy=False), action=PropertyValueSet.return_lower_value)
]

person_basic_keyword_rules = [
    KeywordRule(condition=(person_entity + Star(Any(), greedy=False) + where + birth_place + Star(Any(), greedy=False)) | (person_entity +
                                                                                                                           Star(Any(), greedy=False) + birth_place + Star(Any(), greedy=False)), action=PropertyValueSet.return_birth_place_value),
    KeywordRule(condition=person_entity + Star(Disjunction(Any(), where), greedy=False) +
                birth + Star(Any(), greedy=False), action=PropertyValueSet.return_birth_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + english_name +
                Star(Any(), greedy=False), action=PropertyValueSet.return_english_name_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + introduction +
                Star(Any(), greedy=False), action=PropertyValueSet.return_person_introduction_value),
    # vivire card additional person basic
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + blood_type +
                Star(Any(), greedy=False), action=PropertyValueSet.return_blood_type_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + zodiac_sign +
                Star(Any(), greedy=False), action=PropertyValueSet.return_zodiac_sign_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + haki_type +
                Star(Any(), greedy=False), action=PropertyValueSet.return_haki_type_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + height +
                Star(Any(), greedy=False), action=PropertyValueSet.return_height_value),
]

movie_basic_keyword_rules = [
    KeywordRule(condition=movie_entity + Star(Any(), greedy=False) + introduction +
                Star(Any(), greedy=False), action=PropertyValueSet.return_movie_introduction_value),
    KeywordRule(condition=movie_entity + Star(Any(), greedy=False) + release +
                Star(Any(), greedy=False), action=PropertyValueSet.return_release_value),
    KeywordRule(condition=movie_entity + Star(Any(), greedy=False) + rating +
                Star(Any(), greedy=False), action=PropertyValueSet.return_rating_value),
]

food_basic_keyword_rules = [
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + subtype +
                Star(Any(), greedy=False), action=PropertyValueSet.return_subtype_value),
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + material +
                Star(Any(), greedy=False), action=PropertyValueSet.return_material_value),
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + makestep +
                Star(Any(), greedy=False), action=PropertyValueSet.return_makesteps_value),
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + main_component +
                Star(Any(), greedy=False), action=PropertyValueSet.return_main_value),
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + excipient +
                Star(Any(), greedy=False), action=PropertyValueSet.return_excipient_value),
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + ingredient +
                Star(Any(), greedy=False), action=PropertyValueSet.return_ingredient_value),
    KeywordRule(condition=food_entity + Star(Any(), greedy=False) + feature +
                Star(Any(), greedy=False), action=PropertyValueSet.return_features_value),
    KeywordRule(condition=makestep + Star(Any(), greedy=False) + food_entity +
                Star(Any(), greedy=False), action=PropertyValueSet.return_makesteps_value),
]
