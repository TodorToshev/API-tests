import unittest
import requests
import re

# Въведете subdomain.
subdomain = "<subdomain>"

# Въведете имейл.
email = "<email>"

# Въведете парола.
password = "<password>"


LOGIN_URL = "https://" + subdomain + ".kanbanize.com/index.php/api/kanbanize/login/"
NEW_TASK_URL = (
    "https://" + subdomain + ".kanbanize.com/index.php/api/kanbanize/create_new_task/"
)
GET_TASK_URL = (
    "https://" + subdomain + ".kanbanize.com/index.php/api/kanbanize/get_task_details/"
)
MOVE_TASK_URL = (
    "https://" + subdomain + ".kanbanize.com/index.php/api/kanbanize/move_task/"
)
GET_TASK_URL = (
    "https://" + subdomain + ".kanbanize.com/index.php/api/kanbanize/get_task_details"
)
DELETE_TASK_URL = (
    "https://" + subdomain + ".kanbanize.com/index.php/api/kanbanize/delete_task/"
)

response = requests.post(LOGIN_URL, json={"email": email, "pass": password})
content = response.text

# Съхранява API Key за следващи заявки.
key = re.findall("<apikey>(.*[^\s]+\s*)<\/apikey>", content)[0]

# Създава карта по зададените параметри.
task_created_response = requests.post(
    NEW_TASK_URL,
    headers={"apikey": key},
    json={
        "boardid": "1",
        "title": "Test task",
        "description": "Task description",
        "priority": "High",
        "assignee": "User",
        "color": "FFCC00",
        "tags": "tag1 tag2",
        "deadline": "2011-12-13",
        "position": 2,
        "returntaskdetails": 1,
    },
)

# Взима детайли на новата карта, които после да сравни в друга заявка.
created_task_details = re.findall(
    "<details>(.*[^\s]+\s*)<\/details>", task_created_response.text
)[0]

# ID на карта, по който ще се извършват заявки.
new_task_id = re.findall("<id>(.*[^\s]+\s*)<\/id>", task_created_response.text)[0]


class TestAPICardCreated(unittest.TestCase):
    def test_card_created_with_specified_parameters(self):
        """
        Проверка дали картата е била създадена,
        дали е на очакваната позиция
        и с очакваните параметри.
        """

        response = requests.post(
            GET_TASK_URL,
            headers={"apikey": key},
            json={"boardid": "1", "taskid": new_task_id},
        )

        # Сравняване на детайлите на картата от отговора с детайлите, зададени при създаване.
        current_task_details = re.findall("<xml>(.*[^\s]+\s*)<\/xml>", response.text)[0]
        self.assertEqual(created_task_details, current_task_details)

    def test_change_card_position(self):
        """Да се премести създадената картата на нова позиция."""
        response = requests.post(
            MOVE_TASK_URL,
            headers={"apikey": key},
            json={"boardid": "1", "taskid": new_task_id, "position": "3"},
        )
        self.assertEqual(response.status_code, 200)

    def test_is_card_on_new_position(self):
        """В отделна заявка да се провери дали картата е на новата позиция."""
        response = requests.post(
            GET_TASK_URL,
            headers={"apikey": key},
            json={"boardid": "1", "taskid": new_task_id},
        )
        content = response.text
        position = re.findall("<position>(.*[^\s]+\s*)<\/position>", content)[0]
        self.assertEqual(position, "3")


class TestAPIDeleteOperations(unittest.TestCase):
    def test_1_delete_card(self):
        """Да се изтрие картата."""
        response = requests.post(
            DELETE_TASK_URL,
            headers={"apikey": key},
            json={"boardid": "1", "taskid": new_task_id},
        )

        self.assertEqual(response.status_code, 200)

    def test_2_card_has_been_deleted(self):
        """В отделна заявка да се провери дали картата е била изтрита."""
        response = requests.post(
            GET_TASK_URL,
            headers={"apikey": key},
            json={"boardid": "1", "taskid": new_task_id},
        )
        result = re.findall("<Error>(.*[^\s]+\s*)<\/Error>", response.text)[0]

        """
        При заявка за карта, която не съществува, отговорът е HTTP 400 Bad Request, 
        а не 404 Not Found. Затова сравнявам не с response_code, а с текста от отговора -
        "The specified task does not exist."
        """
        self.assertEqual(result, "The specified task does not exist.")


if __name__ == "__main__":
    unittest.main()
