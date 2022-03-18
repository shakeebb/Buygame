from typing import Optional

import pygame_widgets
import pygame
from pygame_widgets.textbox import TextBox
from pygame.constants import KEYUP, K_ESCAPE, VIDEORESIZE

from common.gameconstants import NL_DELIM, INIT_TILE_SIZE, TILE_ADJ_MULTIPLIER, FPS, Colors, LINE_CONT
from common.gamesurvey import PGGQs, GameSurveyQs, SurveyGridQHeaders, QHeader, PGIQs, SURVEY_QSEQ_DELIM, \
    SURVEY_Qs_DELIM, SURVEY_Qitxt_DELIM, serialize_survey_grid_result, deserialize_survey_input_result, \
    serialize_survey_input_result, deserialize_survey_grid_result
from common.logger import logger, log
from gui.button import RadioButton, TextButton
from gui.gui_common.display import Display
from gui.gui_common.fontmixin import FontMixin
from gui.gui_common.subsurface import SubSurface


class SurveyQuestion:
    def __init__(self):
        pass

    def draw(self, surface):
        pass

    def mouse_down(self, mouse):
        pass

    def mouse_up(self, mouse):
        pass

    def key_up(self, event: pygame.event.Event):
        pass

    def end_group(self):
        pass

    def has_next(self):
        pass

    def move_next(self):
        pass

    def has_prev(self):
        pass

    def move_prev(self):
        pass

    def notify_events(self, events):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def str_result(self) -> str:
        pass


class MultilineTextBox:
    def __init__(self, surface, x, y, width, height, lines, **kwargs):
        self.surface = surface
        self.line_texts: [TextBox] = []
        self.lt_pos = -1
        self.x, self.y = x, y
        self.w, self.h = width, height // lines
        self.lines = lines
        self.kwargs = kwargs
        self.kwargs["onSubmit"] = self.on_submit
        self.create_line = False
        self.offset = 5
        self.shdw = 7
        self.borderColour = [
            Colors.LTS_GRAY.value,
            Colors.LTR_GRAY.value,
            Colors.GRAY.value,
        ]
        self.borderWidth = [
            20,
            20,
            1,
        ]
        filloffset = self.offset + (self.shdw - self.offset) / 2
        self.borderRects = [
            pygame.Rect(self.x - self.shdw, self.y - self.shdw, width + self.shdw * 2, height + self.shdw * 2),
            pygame.Rect(self.x - filloffset, self.y - filloffset, width + filloffset * 2, height + filloffset * 2),
            pygame.Rect(self.x - self.offset, self.y - self.offset, width + self.offset * 2, height + self.offset * 2),
        ]
        self.selected = False

    def set_selected(self, lineno=0, _s=True):
        self.selected = _s
        b = self.line_texts[lineno]
        b.enable() if _s else b.disable()
        b.selected = b.showCursor = _s
        self.lt_pos = lineno if _s else self.lt_pos

    def add_new_line(self, num_actual_lines):
        for _ in range(num_actual_lines):
            yoffset = self.y + (len(self.line_texts) * (self.h + self.offset))
            t = TextBox(self.surface, self.x, yoffset, self.w, self.h, **self.kwargs)
            t.selected = t.showCursor = False
            t.cursorOffsetTop = 0
            t.textOffsetBottom = 0
            self.line_texts.append(t)

    def draw(self, _):
        for rect, color, bw in zip(self.borderRects, self.borderColour, self.borderWidth):
            pygame.draw.rect(self.surface, color, rect, width=1)

    def on_submit(self):
        pass
        # if len(self.line_texts) < 8 and not self.create_line:
        #     self.create_line = True

    def deselect(self):
        # disable every line
        [self.set_selected(lineno=i, _s=False) for i, _ in enumerate(self.line_texts)]

    def move_to_next_line(self, create_new=False):
        if self.lt_pos < len(self.line_texts) - 1 and \
                (create_new or len(self.line_texts[self.lt_pos + 1].text) > 0):
            self.set_selected(self.lt_pos, False)
            pygame.event.clear(pygame.KEYUP)
            self.lt_pos += 1
            self.set_selected(self.lt_pos, True)

    def move_to_prev_line(self):
        if self.lt_pos > 0:
            self.set_selected(self.lt_pos, False)
            pygame.event.clear(pygame.KEYUP)
            cur_pos = self.line_texts[self.lt_pos].cursorPosition
            self.lt_pos -= 1
            tb = self.line_texts[self.lt_pos]
            tb.cursorPosition = min(len(tb.text), cur_pos)
            self.set_selected(self.lt_pos, True)

    def has_max_length_reached(self):
        tb = self.line_texts[self.lt_pos]
        return tb.maxLengthReached and tb.cursorPosition == len(tb.text)

    def mouse_up(self, mouse):
        mx, my = mouse

        def is_line_clicked(_tb: TextBox):
            x, y = _tb.getX(), _tb.getY()
            return (x < mx < x + _tb.getWidth()) and \
                   (y < my < y + _tb.getHeight() + self.offset)

        if self.borderRects[0].collidepoint(*mouse):
            for i, tb in enumerate(self.line_texts):
                if is_line_clicked(tb):
                    self.set_selected(lineno=i, _s=True)
                    break
            return True

        return False

    def enable(self):
        for e in self.line_texts:
            e.enable()
            e.show()

    def disable(self):
        for e in self.line_texts:
            e.disable()
            e.hide()

    def get_text_str(self):
        return "\"" + "\n".join(["".join([_c for _c in _l.text]) for _l in self.line_texts]) + "\""

    def get_ser_text(self):
        return "\"" + \
               NL_DELIM.join(["".join([_c for _c in _l.text]).replace(NL_DELIM, '') for _l in self.line_texts]) + \
               "\""


class SurveyQuestionInputText(SurveyQuestion):
    class InputSection(FontMixin, Display):
        def __init__(self, parent, question: GameSurveyQs, max_input_len, h, v, w, ht):
            FontMixin.__init__(self)
            Display.__init__(self, h, v, w, ht)
            self.set_font_name("verdana")
            self.set_font_size(17)

            self.p = parent
            self.q = question
            self.ques = self.render_texts(self.q.q)
            self.tot_ques_font_ht = self.ques[0].get_height() * 1.1 * len(self.ques)
            self.mx_len = max_input_len
            self.text_box = MultilineTextBox(self.p.get_surface(),
                                             self.x,
                                             self.y,
                                             self.width,
                                             self.height,
                                             10,
                                             font=self.font,
                                             colour=Colors.WHITE.value,
                                             borderColour=Colors.LTR_GRAY.value,
                                             textColour=Colors.BLACK.value,
                                             radius=0, borderThickness=0)
            self.text_box.add_new_line(8)
            self.user_text = ""
            self.chars = 0
            self.enabled = False

        def set_input_selected(self, _s=True):
            self.text_box.set_selected(_s=_s)

        def enable(self):
            self.text_box.enable()
            self.enabled = True

        def disable(self):
            self.text_box.disable()
            self.enabled = False

        def draw(self, surface):
            if not self.enabled:
                return

            # font_pos = (self.x, self.y)
            tot_l = len(self.ques)
            per_row_ht = self.tot_ques_font_ht / len(self.ques)
            for i, qs in enumerate(self.ques, -1):
                surface.blit(qs, (self.x, self.y - ((tot_l - i) * per_row_ht)))
            self.text_box.draw(None)

        def str_result(self):
            return f"{self.q.__str__()}," + self.text_box.get_text_str()

        def get_user_inputs(self):
            return self.q, self.text_box.get_ser_text()

    def __init__(self, ssurface: SubSurface):
        super().__init__()
        self.ssurface = ssurface
        self.inputs: [SurveyQuestionInputText.InputSection] = []
        self.inputs_pos = -1
        # self.menu: Optional[thorpy.Menu] = None
        # self.thorpy_box = None

    def enable(self):
        [i.enable() for i in self.inputs]

    def disable(self):
        [i.disable() for i in self.inputs]

    def has_next(self):
        return False

    def has_prev(self):
        return False

    def draw(self, surface):
        [i.draw(surface) for i in self.inputs]

    def add_survey_question(self, ques: GameSurveyQs, max_input_len):
        block_sz = len(self.inputs) * (8 * TILE_ADJ_MULTIPLIER)
        self.inputs.append(
            SurveyQuestionInputText.InputSection(
                self, ques, max_input_len,
                8.5 * TILE_ADJ_MULTIPLIER,
                (3 * TILE_ADJ_MULTIPLIER) + block_sz,
                20 * TILE_ADJ_MULTIPLIER,
                5.5 * TILE_ADJ_MULTIPLIER
            ))

    def mouse_down(self, mouse):
        pass

    def mouse_up(self, mouse):
        [_in.text_box.deselect() for _in in self.inputs]
        for i, _in in enumerate(self.inputs):
            if _in.text_box.mouse_up(mouse):
                self.inputs_pos = i
                break

    def key_up(self, event: pygame.event.Event):
        if event.type == pygame.KEYUP:
            tb = self.inputs[self.inputs_pos].text_box
            if event.key == pygame.K_DOWN:
                tb.move_to_next_line()
            elif event.key == pygame.K_UP:
                tb.move_to_prev_line()
            elif event.key == pygame.K_TAB:
                pass
            elif event.key == pygame.K_RETURN:
                tb.move_to_next_line(create_new=True)
            elif tb.has_max_length_reached():
                tb.move_to_next_line(create_new=True)

    def end_group(self):
        self.inputs_pos = 0
        self.inputs[self.inputs_pos].set_input_selected()
        # self.thorpy_box = thorpy.Box(elements=list(map(lambda x: x.slider, self.inputs)))
        # box = self.thorpy_box
        # # we regroup all elements on a menu, even if we do not launch the menu
        # self.menu = thorpy.Menu(box)
        # # important : set the screen as surface for all elements
        # for element in self.menu.get_population():
        #     element.surface = self.ssurface.surface
        # # use the elements normally...
        # box.set_topleft((100, 100))
        # box.blit()
        # box.update()
        pass

    def notify_events(self, events):
        # self.menu.react(events)
        pass

    def get_surface(self):
        return self.ssurface.surface

    def str_result(self):
        return SURVEY_Qs_DELIM.join([_i.str_result() for _i in self.inputs])

    def get_result(self) -> [(GameSurveyQs, str)]:
        res: [(GameSurveyQs, str)] = []
        [res.append(_i.get_user_inputs()) for _i in self.inputs]
        return res


class SurveyQuestionGrid(FontMixin, SurveyQuestion):
    class Row(FontMixin, Display):
        def __init__(self, parent, font_size,
                     question: GameSurveyQs,
                     h_margin,
                     v_margin,
                     width,
                     lineoffset=1.5,
                     num_rb_options=0,
                     idnum=0):
            FontMixin.__init__(self)
            self.lineoffset = lineoffset
            self.set_font_size(font_size)
            self.question = question
            self.q_ft = self.render_texts(self.question.q)
            self.total_height_cells = -1
            self.set_total_height_cells()
            Display.__init__(self, h_margin, v_margin, width, self.total_height_cells)
            self.parent: SurveyQuestionGrid = parent
            self.idnum = idnum
            self.o: RadioButton = RadioButton(h_margin + 32, v_margin, 30, 2,
                                              text_offset=(0, 0),
                                              option_offset=(.5, 3.4),
                                              horizontal=True)
            [self.o.add_option(" ", show_caption=False, default_sel=2) for _ in range(num_rb_options)]

        def set_total_height_cells(self):
            font_ht = sum(map(lambda fs: fs.get_height(), self.q_ft))
            line_space_ht = 1 * self.lineoffset * INIT_TILE_SIZE
            self.total_height_cells = (font_ht + line_space_ht) // INIT_TILE_SIZE

        def draw(self, surface):
            for i, fs in enumerate(self.q_ft):
                font_pos = (self.x, self.y + (i * self.lineoffset * INIT_TILE_SIZE))
                surface.blit(fs, font_pos)
            self.o.draw(surface) if self.o is not None else None

        def get_user_inputs(self, h: QHeader) -> (PGGQs, QHeader):
            h.chosen = self.o.get_chosen_option_value()
            return self.question, h

    class QuestionGroup(FontMixin):
        def __init__(self, parent, start_x, start_y):
            super().__init__()
            self.parent: SurveyQuestionGrid = parent
            self.survey_questions: [SurveyQuestionGrid.Row] = []
            self.h_margin_cells, self.v_margin_cells = start_x, start_y
            self.questions: [GameSurveyQs] = []
            self.first_col_width, _ = Display.coord(18 * TILE_ADJ_MULTIPLIER, 0)

        def add_question(self, question: GameSurveyQs):
            self.questions.append(question)

        def draw(self, surface):
            [row.draw(surface) for row in self.survey_questions]

        def dountil(self, true_condition, action=None):
            for _r in self.survey_questions:
                if true_condition(_r):
                    action(_r) if action is not None else None
                    break

        def mouse_down(self, mouse):
            self.dountil(lambda _r: _r.o.click(*mouse))

        def mouse_up(self, mouse):
            self.dountil(lambda _r: _r.o.click(*mouse))

        def end_group(self):
            from functools import reduce
            lines = map(lambda x: (len(x.strip()), x),
                        reduce(lambda a, b: a + b,
                               map(lambda q: q.q.split(NL_DELIM), self.questions)))
            _, mx_text = max(lines, key=lambda x: x[0])
            # tot_lines = len(list(reduce(lambda a, b: a + b,
            #                             map(lambda q: q.split(NL_DELIM), self.questions)))) + len(self.questions)
            fsz = Display.get_target_fontsz(self.font_name, self.font_size, True, str(mx_text),
                                            self.first_col_width)
            self.set_font_size(fsz)
            # h = self.render_text(str(mx_text))[0].get_rect().height
            lineoffset = 1.5  # ((tot_lines * h) / INIT_TILE_SIZE)/tot_lines
            prev_row_ht = 0
            for i, question in enumerate(self.questions):
                v_offset = prev_row_ht if i != 0 else \
                    self.v_margin_cells
                sqr = SurveyQuestionGrid.Row(self, fsz, question,
                                             self.h_margin_cells,
                                             v_offset,
                                             self.first_col_width,
                                             lineoffset=lineoffset,
                                             num_rb_options=self.parent.cols,
                                             idnum=len(self.survey_questions))
                prev_row_ht = sqr.ymargin()
                self.survey_questions.append(sqr)

    def __init__(self, parent, h: SurveyGridQHeaders):
        FontMixin.__init__(self)
        SurveyQuestion.__init__(self)
        self.parent: Survey = parent
        self.gqh: SurveyGridQHeaders = h
        # Display.__init__(self, 1, 1, 20, 20)
        header = h.h.header
        self.cols = len(header)
        mx_lines_per_col = max(map(lambda x: len(x.split(NL_DELIM)), header))
        self.header = [[] for _ in range(mx_lines_per_col)]
        for e in header:
            c_arr = e.split(NL_DELIM)
            for _i, _h in enumerate(self.header):
                t = c_arr[_i] if _i < len(c_arr) else " "
                _h.append(self.render_texts(t)[0])
        # self.header = [(_ci, _ct) for _ci, _ct in enumerate(column_template)]

        self.question_group: [SurveyQuestionGrid.QuestionGroup] = []
        self.q_grp_pos = 0
        self.grp_render_cells = (5, 8)

    def mouse_down(self, mouse):
        self.question_group[self.q_grp_pos].mouse_down(mouse)

    def mouse_up(self, mouse):
        self.question_group[self.q_grp_pos].mouse_up(mouse)

    def has_next(self):
        return self.q_grp_pos < len(self.question_group) - 1

    def move_next(self):
        self.q_grp_pos += 1

    def has_prev(self):
        return self.q_grp_pos > 0

    def move_prev(self):
        self.q_grp_pos -= 1

    def draw_header(self, surface):
        frst_col = self.question_group[0].first_col_width
        prev_x_len = [0 for _ in range(len(self.header[0]))]
        for y, row in enumerate(self.header):
            for x, col in enumerate(row):
                cum_x_offset = frst_col + sum([prev_x_len[a] for a in range(x)])
                st_x, st_y = Display.coord(self.grp_render_cells[0], self.grp_render_cells[1] - 6)
                font_pos = (cum_x_offset + (x * INIT_TILE_SIZE), st_y + (y * 1.5 * INIT_TILE_SIZE))
                prev_x_len[x] = col.get_width() if prev_x_len[x] < col.get_width() else prev_x_len[x]
                surface.blit(col, font_pos)

        # [he.draw(surface) for h_row in self.header for he in h_row]

    def draw(self, surface):
        self.draw_header(surface)
        self.question_group[self.q_grp_pos].draw(surface)

    def add_group(self):
        _grp = SurveyQuestionGrid.QuestionGroup(self, *self.grp_render_cells)
        self.question_group.append(_grp)
        return _grp

    def get_result(self) -> [(GameSurveyQs, QHeader)]:
        res: [(GameSurveyQs, QHeader)] = []
        for qg in self.question_group:
            [
                res.append(r.get_user_inputs(self.gqh.h.__copy__()))
                for r in qg.survey_questions
            ]
        return res

    def str_result(self):
        return "\n".join([f"{q},{r}" for q, r in self.get_result()])


class Survey(SubSurface):
    def __init__(self, submit_action: (), has_parent=True):
        super(Survey, self).__init__()
        self._layer = SubSurface._SS_BASE_LAYER
        self.s_questions_seq: [SurveyQuestion] = []
        self.s_questions_pos = 0
        h_mrg, v_mrg = self.xmargin() - 12, self.ymargin() - 5
        self.prev_button = TextButton(h_mrg - (4 * TILE_ADJ_MULTIPLIER),
                                      v_mrg,
                                      7, 3, Colors.GREEN,
                                      "prev",
                                      visual_effects=True)
        self.next_button = TextButton(h_mrg,
                                      v_mrg,
                                      7, 3, Colors.GREEN,
                                      "next",
                                      visual_effects=True)

        self.prev_button.hide()
        self.submit = False
        self.submit_act = submit_action
        self.run = True
        self.has_parent = has_parent

    def main(self, input_game=None):
        clock = pygame.time.Clock()
        from gui.gameui import GameUI
        assert input_game is None or isinstance(input_game, GameUI)
        g: GameUI = input_game
        logger.reset()
        while self.run:
            clock.tick(FPS)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse = self.mousexy()
                    self.mouse_down(mouse)

                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse = self.mousexy()
                    self.mouse_up(mouse)
                    pygame.event.clear([pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.KEYUP])

                    #
                    # if self.login_button is not None and \
                    #         self.login_button.click(ss_mx, ss_my):
                    #     self.login_button.mouse_up()
                    #     self.login()
                    #     continue
                    #
                    # if self.user_choices is not None:
                    #     self.user_choices.click(ss_mx, ss_my)
                    #     continue

                elif event.type == pygame.QUIT or \
                        (event.type == KEYUP and event.key == K_ESCAPE):
                    if not self.has_parent:
                        self.run = False
                        pygame.quit()
                        quit()

                elif event.type == VIDEORESIZE:
                    # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    Display.resize(event, g.refresh_resolution) if g is not None else None
                elif event.type == pygame.KEYUP:
                    self.s_questions_seq[self.s_questions_pos].key_up(event)
                    # if event.key == pygame.K_RETURN:
                    #     self.move_next_control(event)
                    # else:
                    #     pass

            self.draw(events)

    def draw(self, events):
        if not self.has_parent:
            Display.surface().fill(Colors.BLACK.value)
        super().draw(events)
        self.prev_button.draw(self.surface)
        self.next_button.draw(self.surface)
        self.s_questions_seq[self.s_questions_pos].draw(self.surface)
        pygame_widgets.update(events)
        pygame.display.update()

    def mouse_down(self, mouse):
        if self.next_button.click(*mouse):
            self.next_button.mouse_down()
            return
        elif self.prev_button.click(*mouse):
            self.prev_button.mouse_down()
            return

        ce = self.s_questions_seq[self.s_questions_pos]
        ce.mouse_down(mouse)

    def mouse_up(self, mouse):
        ce = self.s_questions_seq[self.s_questions_pos]
        if self.next_button.click(*mouse):
            try:
                if self.submit:
                    self.submit_survey()
                    return

                if ce.has_next():
                    ce.move_next()
                    return

                if self.has_next():
                    ce.disable()
                    self.s_questions_pos += 1
                    ce = self.s_questions_seq[self.s_questions_pos]
                    ce.enable()
            finally:
                if not self.has_next():
                    self.next_button.set_text("submit")
                    self.submit = True

                self.prev_button.show()
                self.next_button.mouse_up()
        elif self.prev_button.click(*mouse):
            try:
                if ce.has_prev():
                    ce.move_prev()
                    return

                if self.has_prev():
                    ce.disable()
                    self.s_questions_pos -= 1
                    ce = self.s_questions_seq[self.s_questions_pos]
                    ce.enable()
            finally:
                if not self.has_prev():
                    self.prev_button.hide()

                self.submit = False
                self.next_button.set_text("next")
                self.prev_button.mouse_up()
        elif ce.mouse_up(mouse):
            pass

    def has_prev(self):
        return self.s_questions_pos > 0 or self.s_questions_seq[self.s_questions_pos].has_prev()

    def has_next(self):
        return self.s_questions_pos < len(self.s_questions_seq) - 1

    def add_post_game_survey_grid(self):
        q1 = "1.	Please rate the below sentences:"
        sqg = SurveyQuestionGrid(self, SurveyGridQHeaders.H1)

        questions = [
            [PGGQs.Q1, PGGQs.Q2, PGGQs.Q3, PGGQs.Q4, PGGQs.Q5, PGGQs.Q6],
            [PGGQs.Q7, PGGQs.Q8, PGGQs.Q9, PGGQs.Q10, PGGQs.Q11, PGGQs.Q12],
            [PGGQs.Q13, PGGQs.Q14, PGGQs.Q15, PGGQs.Q16],
            [PGGQs.Q17, PGGQs.Q18, PGGQs.Q19],
        ]

        for _q_grp in questions:
            _sqg_grp = sqg.add_group()
            for _q in _q_grp:
                _sqg_grp.add_question(_q)
            _sqg_grp.end_group()

        self.s_questions_seq.append(sqg)

    def add_post_game_survey_inputs(self):
        sit = SurveyQuestionInputText(self)
        sit.add_survey_question(PGIQs.Q1, 450)
        sit.add_survey_question(PGIQs.Q2, 450)
        sit.end_group()
        sit.disable()

        self.s_questions_seq.append(sit)

    def submit_survey(self):
        g = self.s_questions_seq[0]
        s1 = serialize_survey_grid_result(g.gqh, g.get_result())
        s2 = serialize_survey_input_result(self.s_questions_seq[1].get_result())
        msg = SURVEY_QSEQ_DELIM.join([s1, s2])
        log("SUBMIT SURVERY\n" + msg)
        if self.submit_act is not None:
            self.submit_act(msg)
        else:
            ds1, ds2 = msg.split(SURVEY_QSEQ_DELIM)
            sg = deserialize_survey_grid_result(ds1)
            si = deserialize_survey_input_result(ds2)
            print("SB: DESER values to track")
            print("\n".join([f"{q},{r}" for q, r in sg]))
            print("\n".join([f"{q},{t}" for q, t in si]))
        self.run = False


if __name__ == '__main__':
    Display.init()

    s = Survey(None, False)
    s.add_post_game_survey_grid()
    s.add_post_game_survey_inputs()
    s.main()
