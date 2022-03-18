from enum import Enum, auto

from common.gameconstants import NL_DELIM, LINE_CONT

SURVEY_QSEQ_DELIM = ';[[[]]];'
SURVEY_Qs_DELIM = ';'
SURVEY_Qs_HDR_DELIM = '--;--'
SURVEY_Qitxt_DELIM = ';--;'


class QHeader:
    def __init__(self, header: [str]):
        self.header: [str] = header
        self.chosen = -1

    def __copy__(self):
        new = QHeader(self.header)
        new.chosen = -1
        return new

    def __repr__(self):
        if self.chosen >= 0:
            return "\"" + self.header[self.chosen].replace(NL_DELIM, '\n') + "\""
        else:
            return ""

    def __str__(self):
        return self.__repr__()

    def set_chosen(self, c: int):
        self.chosen = c
        return self


class SurveyGridQHeaders(Enum):
    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, h: [str]):
        self.h = QHeader(h)

    H1 = ([f"Strongly{NL_DELIM}Agree",
           f"Somewhat{NL_DELIM}Agree",
           f"Neither{NL_DELIM}Agree/{NL_DELIM}Disagree",
           f"Somewhat{NL_DELIM}Disagree",
           f"Strongly{NL_DELIM}Disagree"])

    @classmethod
    def parse_msg_string(cls, enum_id: int):
        return cls(0)

    # C1 = (auto(), f"Strongly{NL_DELIM}Agree")
    # C2 = (auto(), f"Somewhat{NL_DELIM}Agree")
    # C3 = (auto(), f"Neither{NL_DELIM}Agree/{NL_DELIM}Disagree")
    # C4 = (auto(), f"Somewhat{NL_DELIM}Disagree")
    # C5 = (auto(), f"Strongly{NL_DELIM}Disagree")


class GameSurveyQs(Enum):
    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__)  # note no + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, q):
        self.q = q

    def __repr__(self):
        return "\"" + \
               '\n'.join([x.strip().replace(LINE_CONT, ' ') for x in self.q.split(NL_DELIM)]) + \
               "\""

    def __str__(self):
        return self.__repr__()


class PGGQs(GameSurveyQs):
    Q1 = "The game was harder than I expected."
    Q2 = "I am an expert in this game."
    Q3 = "I did better than I normally do in word games."
    Q4 = "I was unlucky today."
    Q5 = f"I frequently received highly rare letters{NL_DELIM}\
        (e.g., Z with 4 pips, W with 3 pips, etc.)."
    Q6 = f"Making words with high pip letters{NL_DELIM}\
        (e.g., Z with 4 pips, W with 3 pips, etc.){NL_DELIM}\
        was difficult. "
    Q7 = "My opponent was a pro in this game."
    Q8 = "Luck is an important factor in this game."
    Q9 = "I couldn’t focus my attention on the game."
    Q10 = f"Receiving a batch of letters with high pips {NL_DELIM}\
        (i.e., highly rare letters){NL_DELIM}\
         makes things more difficult in this game."
    Q11 = f"At times I waited for letters that were highly rare  {NL_DELIM}\
        because I recognized an expensive word opportunity."
    Q12 = f"I sometimes recognized a word that can be constructed {NL_DELIM}\
        with my existing batch of letters plus a few letters that {NL_DELIM}\
        were lacking in my batch. {NL_DELIM}\
        I then started waiting for the missing letters {NL_DELIM}\
        to make this word."
    Q13 = f"Making words with low pips {NL_DELIM}\
        (e.g., A with 1 pip, K with 2 pips) {NL_DELIM}\
        is easier."
    Q14 = f"Making words with low pips {NL_DELIM}\
        (e.g., A with 1 pip, K with 2 pips) {NL_DELIM}\
        requires creative thinking."
    Q15 = f"Making words with high pips {NL_DELIM}\
        (e.g., Z with 4 pips, W with 3 pips, etc.){NL_DELIM}\
         is easier."
    Q16 = f"Making words with high pips {NL_DELIM}\
        (e.g., Z with 4 pips, W with 3 pips, etc.){NL_DELIM}\
         requires creative thinking."
    Q17 = f"I preferred not purchasing the batch {NL_DELIM}\
        of letters with high pips."
    Q18 = f"I didn’t miss purchasing cheap batches of letters {NL_DELIM}\
        (e.g., A with 1 pip, K with 2 pips)."
    Q19 = "I couldn’t use the Wild cards wisey."

    @classmethod
    def parse_msg_string(cls, enum_id: int):
        return cls(enum_id)


def serialize_survey_grid_result(h: SurveyGridQHeaders, result: [(GameSurveyQs, QHeader)]):
    return str(h.value) + SURVEY_Qs_HDR_DELIM + SURVEY_Qs_DELIM.join([f"{q.value},{r.chosen}" for q, r in result])


def deserialize_survey_grid_result(ser_obj: str):
    res: [GameSurveyQs, QHeader] = []
    hdr, bdy = ser_obj.split(SURVEY_Qs_HDR_DELIM)
    h = SurveyGridQHeaders.parse_msg_string(hdr)
    for qs in bdy.split(SURVEY_Qs_DELIM):
        q, rc = qs.split(',')
        res.append((PGGQs.parse_msg_string(int(q)),
                    h.h.__copy__().set_chosen(int(rc))))
    return res


class PGIQs(GameSurveyQs):
    Q1 = f"2. Please briefly state your understanding of the game.{NL_DELIM}\
                    {LINE_CONT} What should be a winning strategy in this game?"
    Q2 = "3. Any further comments:"

    @classmethod
    def parse_msg_string(cls, enum_id: int):
        return cls(enum_id)


def serialize_survey_input_result(result: [(GameSurveyQs, str)]):
    return SURVEY_Qitxt_DELIM.join([f"{q.value}{SURVEY_Qs_DELIM}{t}" for q, t in result])


def deserialize_survey_input_result(ser_obj: str):
    res: [(GameSurveyQs, str)] = []
    import re
    deserpat = re.compile(f"(\\d{1}?){SURVEY_Qs_DELIM}(\".*?\")$", re.M)

    for qt_line in ser_obj.split(SURVEY_Qitxt_DELIM):
        m = deserpat.match(qt_line)
        print(m.groups())
        res.append((PGIQs.parse_msg_string(int(m.group(1))), m.group(2)))
    return res
