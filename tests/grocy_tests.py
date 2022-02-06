import unittest
from discord_chatbot.grocy import get_chore_due_date, get_overdue_chores

class ChoresTestCase(unittest.TestCase):
    def test_get_chore_due_date_single_chore(self):
        messages = get_chore_due_date('Revolution')
        self.assertTrue(messages)
        self.assertEqual(len(messages), 1)
    
    def test_get_chore_due_date_all_chores(self):
        messages = get_chore_due_date()
        self.assertTrue(messages)
        self.assertGreater(len(messages), 1)
    
    def test_get_overdue_chores(self):
        overdue_chores = get_overdue_chores()
        self.assertTrue(overdue_chores)