from __future__ import annotations

from math import ceil

import streamlit as st
from sqlalchemy.orm import Session

from job_finder.db.queries import mark_application_sent, update_job_status


def get_cached_jobs(session: Session, user_id: str):
	cache_key = f"dashboard_jobs_{user_id}"
	if cache_key not in st.session_state:
		from job_finder.db.queries import get_jobs_for_user

		st.session_state[cache_key] = get_jobs_for_user(session, user_id)
	return st.session_state[cache_key]


def update_cached_job(user_id: str, job_id: str, **updates) -> None:
	cache_key = f"dashboard_jobs_{user_id}"
	jobs = st.session_state.get(cache_key, [])
	for job in jobs:
		if job.id == job_id:
			for field, value in updates.items():
				setattr(job, field, value)
			break


def clear_cached_jobs(user_id: str) -> None:
	cache_key = f"dashboard_jobs_{user_id}"
	st.session_state.pop(cache_key, None)
	st.session_state.pop(f"dashboard_new_page_{user_id}", None)
	st.session_state.pop(f"dashboard_saved_page_{user_id}", None)


def _set_job_status(session: Session, user_id: str, job_id: str, status: str) -> None:
	update_job_status(session, job_id, status)
	update_cached_job(user_id, job_id, status=status)


def _mark_job_applied(session: Session, user_id: str, job_id: str, date_value) -> None:
	mark_application_sent(session, job_id, str(date_value))
	update_cached_job(user_id, job_id, application_sent=True, status="applied")


def _page_state_key(user_id: str, section_key: str) -> str:
	return f"dashboard_{section_key}_page_{user_id}"


def _render_pager(user_id: str, section_key: str, current_page: int, total_pages: int) -> None:
	prev_col, label_col, next_col = st.columns([1, 2, 1])

	with prev_col:
		if st.button("◀ Prev", key=f"{section_key}_prev_{user_id}", disabled=current_page <= 0):
			st.session_state[_page_state_key(user_id, section_key)] = current_page - 1
			st.rerun()

	with label_col:
		st.caption(f"Page {current_page + 1} of {total_pages}")

	with next_col:
		if st.button("Next ▶", key=f"{section_key}_next_{user_id}", disabled=current_page >= total_pages - 1):
			st.session_state[_page_state_key(user_id, section_key)] = current_page + 1
			st.rerun()


def _render_job_details(job) -> None:
	st.write(f"**Salary:** {job.salary_min or 'N/A'} - {job.salary_max or 'N/A'} {job.salary_currency or ''}")
	st.write(f"**Posted:** {job.posted_at}")
	if job.url:
		st.markdown(f"[View Job]({job.url})")
	if job.description:
		st.write("**Description:**")
		st.write(job.description[:500])


def _render_new_job_actions(job, user_id: str, session: Session) -> None:
	col1, col2 = st.columns(2)
	col1.button(
		"🟢 Interesting",
		key=f"int_{job.id}",
		on_click=_set_job_status,
		args=(session, user_id, job.id, "saved"),
	)
	col2.button(
		"🔴 Not Interesting",
		key=f"not_{job.id}",
		on_click=_set_job_status,
		args=(session, user_id, job.id, "rejected"),
	)


def _render_saved_job_actions(job, user_id: str, session: Session) -> None:
	col1, col2 = st.columns(2)
	if not job.application_sent:
		date_value = st.date_input("Date applied", key=f"date_{job.id}")
		col1.button(
			"✅ Mark Applied",
			key=f"app_{job.id}",
			on_click=_mark_job_applied,
			args=(session, user_id, job.id, str(date_value)),
		)
	col2.button(
		"🔴 Not Interesting",
		key=f"ni_{job.id}",
		on_click=_set_job_status,
		args=(session, user_id, job.id, "rejected"),
	)


def render_job_section(
	*,
	title: str,
	section_key: str,
	jobs,
	user_id: str,
	session: Session,
	page_size: int,
	empty_message: str,
) -> None:
	if not jobs:
		return

	page_state_key = _page_state_key(user_id, section_key)
	total_pages = max(1, ceil(len(jobs) / page_size))
	current_page = min(st.session_state.get(page_state_key, 0), total_pages - 1)
	st.session_state[page_state_key] = current_page

	st.subheader(title)
	_render_pager(user_id, section_key, current_page, total_pages)

	start_index = current_page * page_size
	end_index = start_index + page_size
	page_jobs = jobs[start_index:end_index]

	if not page_jobs:
		st.info(empty_message)
		return

	for job in page_jobs:
		with st.expander(f"🔹 {job.company} — {job.title}"):
			_render_job_details(job)
			if section_key == "new":
				_render_new_job_actions(job, user_id, session)
			elif section_key == "saved":
				_render_saved_job_actions(job, user_id, session)

