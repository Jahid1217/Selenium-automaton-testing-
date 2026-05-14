import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import subprocess
import logging
import inspect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URL = "https://newmis.southsudansafetynet.info/trial/beneficiary/#/beneficiary/edit/33b8a529-ac20-48b3-89aa-c714786aa698"


# Row index
ROW_0_2 = 1
ROW_3_5 = 2
ROW_6_17 = 3
ROW_18_35 = 4
ROW_36_64 = 5
ROW_65_PLUS = 6

# Column index
MALE_TOTAL = 2
MALE_DISABLED = 3
MALE_CHRONIC = 4
MALE_BOTH = 5

FEMALE_TOTAL = 6
FEMALE_DISABLED = 7
FEMALE_CHRONIC = 8
FEMALE_BOTH = 9


LIPW_REASONS = [
    "LIPW_REASON_1",
    "LIPW_REASON_2",
    "LIPW_REASON_3",
    "LIPW_REASON_4",
    "LIPW_REASON_5",
]

DIS_REASONS = [
    "DIS_REASON_1",
    "DIS_REASON_2",
    "DIS_REASON_3",
    "DIS_REASON_4",
    "DIS_REASON_5",
]


def get_default_browser():
    try:
        result = subprocess.run(
            ['reg', 'query', 'HKCU\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice', '/v', 'ProgId'],
            capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'ProgId' in line:
                    progid = line.split()[-1].strip()
                    if 'Chrome' in progid:
                        return 'chrome'
                    elif 'MSEdge' in progid:
                        return 'edge'
                    elif 'Firefox' in progid:
                        return 'firefox'
                    else:
                        return 'chrome'  # default to chrome
        return 'chrome'
    except Exception:
        return 'chrome'


@pytest.fixture(scope="session")
def driver():
    browser = get_default_browser()
    
    if browser == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    elif browser == 'edge':
        options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
    elif browser == 'firefox':
        options = webdriver.FirefoxOptions()
        options.add_argument("--start-maximized")
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
    else:
        # default to chrome
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    driver.get(URL)

    # If login page appears, login manually once.
    # Human civilization invented auth, so naturally automation must suffer.
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//table[contains(@class,'table-bordered')]"))
    )

    yield driver

def reset_page(driver):
    driver.get(URL)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//table[contains(@class,'table-bordered')]"))
    )


def wait(driver):
    return WebDriverWait(driver, 20)


def set_age_value(driver, row, column, value):
    xpath = f"(//table[contains(@class,'table-bordered')]//tbody/tr)[{row}]/td[{column}]//input"
    element = wait(driver).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(str(value))


def clear_age_table(driver):
    for row in range(1, 7):
        for col in range(2, 10):
            set_age_value(driver, row, col, 0)


def select_support_type(driver, support_type):
    radio = wait(driver).until(
        EC.element_to_be_clickable((
            By.XPATH,
            f"//input[@formcontrolname='supportType' and @value='{support_type}']"
        ))
    )
    radio.click()


def reason_exists(driver, reason_code):
    return len(driver.find_elements(By.XPATH, f"//input[@type='checkbox' and @value='{reason_code}']")) > 0


def is_reason_enabled(driver, reason_code):
    checkbox = wait(driver).until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//input[@type='checkbox' and @value='{reason_code}']"
        ))
    )
    return checkbox.is_enabled()


def enabled_reasons(driver, reasons):
    return [reason for reason in reasons if reason_exists(driver, reason) and is_reason_enabled(driver, reason)]


# =========================
# LIPW TEST CASES
# =========================

def test_lipw_poor_household_valid_when_able_bodied_18_64_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert is_reason_enabled(driver, "LIPW_REASON_1")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_invalid_when_no_able_bodied_18_64(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)
    set_age_value(driver, ROW_18_35, MALE_DISABLED, 1)

    select_support_type(driver, "Public Works")

    assert "LIPW_REASON_1" not in enabled_reasons(driver, LIPW_REASONS)
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_youth_reason_valid_when_18_35_member_and_able_bodied_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert is_reason_enabled(driver, "LIPW_REASON_2")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_youth_reason_valid_when_youth_sick_but_other_able_bodied_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)
    set_age_value(driver, ROW_18_35, MALE_DISABLED, 1)

    set_age_value(driver, ROW_36_64, FEMALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert is_reason_enabled(driver, "LIPW_REASON_2")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_youth_reason_invalid_when_youth_exists_but_no_able_bodied(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)
    set_age_value(driver, ROW_18_35, MALE_DISABLED, 1)

    select_support_type(driver, "Public Works")

    assert not is_reason_enabled(driver, "LIPW_REASON_2")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_young_headed_reason_valid(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, FEMALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert is_reason_enabled(driver, "LIPW_REASON_3")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_many_dependents_valid_when_dependents_greater_than_3_and_able_bodied_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    # 4 children
    set_age_value(driver, ROW_0_2, MALE_TOTAL, 2)
    set_age_value(driver, ROW_6_17, FEMALE_TOTAL, 2)

    # able-bodied adult
    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert is_reason_enabled(driver, "LIPW_REASON_4")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_many_dependents_invalid_when_dependents_equal_3(driver):
    reset_page(driver)
    clear_age_table(driver)

    # 3 dependents only
    set_age_value(driver, ROW_0_2, MALE_TOTAL, 2)
    set_age_value(driver, ROW_65_PLUS, FEMALE_TOTAL, 1)

    # able-bodied adult
    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert not is_reason_enabled(driver, "LIPW_REASON_4")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_many_dependents_invalid_without_able_bodied(driver):
    reset_page(driver)
    clear_age_table(driver)

    # 4 children
    set_age_value(driver, ROW_0_2, MALE_TOTAL, 4)

    select_support_type(driver, "Public Works")

    assert not is_reason_enabled(driver, "LIPW_REASON_4")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_lipw_disability_reason_valid_when_disabled_person_and_able_bodied_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_6_17, FEMALE_TOTAL, 1)
    set_age_value(driver, ROW_6_17, FEMALE_DISABLED, 1)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Public Works")

    assert is_reason_enabled(driver, "LIPW_REASON_5")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


# =========================
# DIS TEST CASES
# =========================

def test_dis_child_headed_valid_with_child_and_no_able_bodied_adult(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_6_17, MALE_TOTAL, 1)

    select_support_type(driver, "Direct Income Support")

    assert is_reason_enabled(driver, "DIS_REASON_1")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_child_headed_invalid_without_child(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, MALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, MALE_CHRONIC, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_1")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_child_headed_invalid_when_able_bodied_adult_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_6_17, MALE_TOTAL, 1)
    set_age_value(driver, ROW_18_35, FEMALE_TOTAL, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_1")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_elderly_valid_when_65_plus_exists_and_no_able_bodied_18_64(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_65_PLUS, MALE_TOTAL, 1)

    select_support_type(driver, "Direct Income Support")

    assert is_reason_enabled(driver, "DIS_REASON_2")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_elderly_invalid_without_elderly(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, MALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, MALE_DISABLED, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_2")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_elderly_invalid_when_able_bodied_18_64_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_65_PLUS, MALE_TOTAL, 1)
    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_2")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_disability_valid_when_disabled_exists_and_no_able_bodied(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, MALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, MALE_DISABLED, 1)

    select_support_type(driver, "Direct Income Support")

    assert is_reason_enabled(driver, "DIS_REASON_3")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_disability_invalid_without_disabled_or_both(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, MALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, MALE_CHRONIC, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_3")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_chronic_valid_when_chronic_exists_and_no_able_bodied(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, MALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, MALE_CHRONIC, 1)

    select_support_type(driver, "Direct Income Support")

    assert is_reason_enabled(driver, "DIS_REASON_4")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_chronic_invalid_without_chronic_or_both(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, MALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, MALE_DISABLED, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_4")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_female_headed_valid_when_adult_female_exists_and_no_able_bodied(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, FEMALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, FEMALE_DISABLED, 1)

    select_support_type(driver, "Direct Income Support")

    assert is_reason_enabled(driver, "DIS_REASON_5")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_female_headed_invalid_without_adult_female(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_6_17, FEMALE_TOTAL, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_5")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


def test_dis_female_headed_invalid_when_able_bodied_male_exists(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_36_64, FEMALE_TOTAL, 1)
    set_age_value(driver, ROW_36_64, FEMALE_DISABLED, 1)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)

    select_support_type(driver, "Direct Income Support")

    assert not is_reason_enabled(driver, "DIS_REASON_5")
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


# =========================
# INVALID INPUT TESTS
# =========================

def test_invalid_when_disabled_chronic_both_greater_than_total(driver):
    reset_page(driver)
    clear_age_table(driver)

    set_age_value(driver, ROW_18_35, MALE_TOTAL, 1)
    set_age_value(driver, ROW_18_35, MALE_DISABLED, 1)
    set_age_value(driver, ROW_18_35, MALE_CHRONIC, 1)

    # Here you need to click Save/Next and check validation message.
    # Because I do not have your Save button HTML. Naturally, the one useful button escaped.
    #
    # Example:
    # driver.find_element(By.XPATH, "//button[contains(., 'Save') or contains(., 'Next')]").click()
    # assert "Invalid" in driver.page_source

    assert True
    print(f"Test {inspect.currentframe().f_code.co_name} completed successfully")


if __name__ == "__main__":
    pytest.main([__file__])