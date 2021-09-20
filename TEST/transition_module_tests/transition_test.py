import sys
from transitions import Machine

class TransitionTest():
    states = ['A', 'B', 'C']

    transitions = [
            {
                'trigger': 'process',
                'source': 'A',
                'dest': 'B',
                'prepare': 'prepare_func',
                'conditions': 'conditions_func',
                'unless': 'unless_func',
                'before': 'before_func',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'B',
                'dest': 'C',
                'prepare': 'prepare_func',
                'conditions': 'conditions_func',
                'unless': 'unless_func',
                'before': 'before_func',
                'after': 'after_func'
                },
            {
                'trigger': 'process',
                'source': 'C',
                'dest': 'A',
                'prepare': 'prepare_func',
                'conditions': 'conditions_func',
                'unless': 'unless_func',
                'before': 'before_func',
                'after': 'after_func'
                }
            ]

    def __init__(self):
        self.machine = Machine(model=self, states=self.states,\
                transitions=self.transitions,\
                prepare_event='machine_preparing_event',
                before_state_change='machine_before_state_change_func',
                after_state_change='machine_after_state_change_func',
                finalize_event='machine_finalizing_event',
                initial='A', send_event=True, queued=True)

    def machine_preparing_event(self, event):
        print('%s: Machine preparing event...' % self.state)

    def machine_before_state_change_func(self, event):
        print('%s: Machine before state change...' % self.state)

    def machine_after_state_change_func(self, event):
        print('%s: Machine after state change...' % self.state)

    def machine_finalizing_event(self, event):
        print('%s: Machine finalizing event...' % self.state)

    def prepare_func(self, event):
        print('%s: Prepare func...' % self.state)

    def conditions_func(self, event):
        print('%s: Conditions func...' % self.state)
        return True

    def unless_func(self, event):
        print('%s: Unless func...' % self.state)
        return False

    def before_func(self, event):
        print('%s: Before func...' % self.state)

    def after_func(self, event):
        print('%s: After func...' % self.state)
        data = input('Enter any key to continue. Q to exit.')
        if data == 'Q':
            sys.exit()

        self.process()

    def after_func_C(self, event):
        print('%s: After func C...' % self.state)

    def on_enter_A(self, event):
        print('%s: On enter ...' % self.state)

    def on_enter_B(self, event):
        print('%s: On enter ...' % self.state)

    def on_enter_C(self, event):
        print('%s: On enter ...' % self.state)

    def on_exit_A(self, event):
        print('%s: On exit ...' % self.state)

    def on_exit_B(self, event):
        print('%s: On exit ...' % self.state)

    def on_exit_C(self, event):
        print('%s: On exit ...' % self.state)

def main():
    tt = TransitionTest()
    print(tt.state)
    tt.process()
    print(tt.state)


    """
    string = 'to_C'
    method_to_call = getattr(tt, string)
    method_to_call()
    """

main()
