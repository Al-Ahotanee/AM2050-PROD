import json
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://127.0.0.1:3000"
PHONE = "09024355355"
PASSWORD = "AM2050-Sandbox-2026!"
OUT = Path("/home/ubuntu/am2050_mobile_audit_375")
SCREENS = OUT / "screens"
OUT.mkdir(parents=True, exist_ok=True)
SCREENS.mkdir(parents=True, exist_ok=True)

ROUTES = [
    ("landing", "/"),
    ("login", "/login"),
    ("workspace", "/workspace"),
    ("households", "/households"),
    ("children", "/children"),
    ("child-registration", "/children/new"),
    ("child-journey", "/child-journey"),
    ("enrollments", "/enrollments"),
    ("attendance", "/attendance"),
    ("learning-records", "/learning-records"),
    ("defaulters", "/defaulters"),
    ("surveys", "/surveys"),
    ("tsangaya", "/tsangaya"),
    ("compliance", "/compliance"),
    ("incentives", "/incentives"),
    ("users", "/users"),
    ("teacher-management", "/teacher-management"),
    ("geography", "/geography"),
    ("settings", "/settings"),
    ("audit", "/audit"),
    ("heatmap", "/heatmap"),
    ("dropout-risk", "/dropout-risk"),
    ("roi", "/roi"),
    ("schools", "/schools"),
    ("teachers", "/teachers"),
    ("classes", "/classes"),
    ("subjects", "/subjects"),
    ("out-of-school", "/out-of-school"),
    ("reports", "/reports"),
    ("cohorts", "/cohorts"),
    ("report-schedules", "/report-schedules"),
]

METRICS_SCRIPT = """
const viewport = { width: window.innerWidth, height: window.innerHeight };
const isVisible = (el) => {
  const style = getComputedStyle(el); const r = el.getBoundingClientRect();
  return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && r.width > 0 && r.height > 0;
};
const elements = [...document.querySelectorAll('a[href], button, input, select, textarea, summary, [role="button"]')]
  .filter(isVisible)
  .map((el) => { const r = el.getBoundingClientRect(); return { tag: el.tagName.toLowerCase(), label: (el.getAttribute('aria-label') || el.innerText || el.placeholder || '').trim().replace(/\\s+/g,' ').slice(0,80), width: Math.round(r.width), height: Math.round(r.height) }; });
const smallTargets = elements.filter((el) => el.width < 44 || el.height < 44);
const tables = [...document.querySelectorAll('table')].filter(isVisible).map((table) => {
  const r = table.getBoundingClientRect(); const parent = table.parentElement; const style = parent ? getComputedStyle(parent) : null;
  return { width: Math.round(r.width), viewportOverflow: r.width > window.innerWidth + 1, parentOverflowX: style ? style.overflowX : null, parentScrollable: parent ? parent.scrollWidth > parent.clientWidth + 1 : false };
});
const docWidth = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
return { viewport, docWidth, horizontalOverflow: docWidth > window.innerWidth + 1, overflowPx: Math.max(0, docWidth - window.innerWidth), bodyHeight: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0), visibleTargets: elements.length, smallTargetCount: smallTargets.length, smallTargets: smallTargets.slice(0,15), tables };
"""

def wait_for_app(driver):
    time.sleep(1.3)
    driver.execute_script("return document.fonts ? document.fonts.ready : Promise.resolve()")
    time.sleep(0.4)

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--hide-scrollbars")
options.add_argument("--window-size=375,812")
options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": 375, "height": 812, "deviceScaleFactor": 1, "mobile": False})
driver.execute_cdp_cmd("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
results = {"viewportTarget": "375x812", "routes": [], "drawer": None, "authentication": {}}
try:
    driver.get(f"{BASE_URL}/login")
    wait_for_app(driver)
    phone = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="0800 000 0000"]')
    password = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Enter your password"]')
    phone.send_keys(PHONE)
    password.send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
    time.sleep(2.2)
    results["authentication"] = {"url": driver.current_url, "passed": "/workspace" in driver.current_url and "Login" not in driver.find_element(By.TAG_NAME, "body").text[:250]}

    for name, route in ROUTES:
        driver.get(f"{BASE_URL}{route}")
        wait_for_app(driver)
        metrics = driver.execute_script(METRICS_SCRIPT)
        body = driver.find_element(By.TAG_NAME, "body").text
        screenshot_path = SCREENS / f"{name}.png"
        driver.save_screenshot(str(screenshot_path))
        results["routes"].append({"name": name, "route": route, "finalUrl": driver.current_url.replace(BASE_URL, ""), "pageTitle": driver.title, "loginRedirect": "STAFF PHONE NUMBER" in body[:500], **metrics})

    driver.get(f"{BASE_URL}/workspace")
    wait_for_app(driver)
    menu = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Open navigation"]')
    menu.click()
    time.sleep(0.35)
    drawer = next(element for element in driver.find_elements(By.CSS_SELECTOR, 'aside') if element.rect["width"] > 0 and element.rect["height"] > 0)
    drawer_metrics = driver.execute_script("const r=arguments[0].getBoundingClientRect(); return { width: Math.round(r.width), height: Math.round(r.height), viewportWidth: innerWidth, viewportHeight: innerHeight, overflowsViewport: r.width > innerWidth || r.height > innerHeight };", drawer)
    driver.save_screenshot(str(SCREENS / "workspace-drawer.png"))
    results["drawer"] = drawer_metrics
finally:
    driver.quit()

(OUT / "audit-results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps({"output": str(OUT / "audit-results.json"), "routeCount": len(results["routes"]), "auth": results["authentication"], "drawer": results["drawer"]}, indent=2))
