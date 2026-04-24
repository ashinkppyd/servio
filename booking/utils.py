# booking/utils.py

SALARY_MAP = {
    "catering_boy": 500,
    "main_boy": 700,
    "supervisor": 900,
    "captain": 1200,
    "juicer": 600,
    "juicer_helper": 400,
    "chef_helper": 650,
    "decoration": 550,
}


def calculate_salary(position):
    return SALARY_MAP.get(position, 500)


def update_worker_progress(worker):
    worker.total_jobs += 1

    if worker.total_jobs >= 50:
        worker.role_level = "captain"
    elif worker.total_jobs >= 35:
        worker.role_level = "supervisor"
    elif worker.total_jobs >= 20:
        worker.role_level = "main_boy"
    worker.save()
