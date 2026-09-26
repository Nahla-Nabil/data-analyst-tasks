# Key insights: Healthcare No-Shows

These figures cover all 106,982 appointments that remain after cleaning (60,270 patients, 29 Apr to 8 Jun 2016).
Each number can be traced to the **KPIs** and **Analysis** sheets of `Healthcare_NoShows_Dashboard.xlsx`.

## KPI scorecard

| KPI | Value |
|---|---|
| Appointments / unique patients | 106,982 / 60,270 (1.78 per patient) |
| No-shows / no-show rate | 21,675 / **20.3%** (attendance 79.7%) |
| Average lead time | 10.2 days. No-shows waited 15.8 days, attendees 8.7 |
| Same-day bookings | 34.7% of volume, **4.7%** no-show |
| Booked 1+ days ahead | **28.5%** no-show |
| SMS coverage of bookings made 1+ days ahead | 49.5% |
| No-show rate if the patient missed before / never missed | **29.4%** / 17.1% |

## Findings

1. **Lead time is the strongest driver.** The no-show rate climbs from 4.7% for same-day bookings to 22.9% at 1–3 days, 32.7% at 15–30 days and 34.4% at 31–60 days. Bookings made 15+ days ahead are 25% of appointments but **41% of all no-shows**.
2. **SMS reminders work, but the raw numbers say the opposite (Simpson's paradox).** Taken overall, SMS patients miss *more* (27.7% vs 16.7%). The reason is that SMS is never sent for same-day bookings, which almost always attend. Compare within the same lead time and SMS lowers no-shows at *every* level, by 1.6 to 7.8 points (for example 30.0% vs 37.0% at 15–30 days). Even so, half of all advance bookings receive no SMS.
3. **Past behaviour predicts the next no-show.** A patient with an earlier no-show misses 29.4% of later appointments, against 17.1% for returning patients with a clean record. 3,157 patients with 2+ no-shows cause 36% of all no-shows.
4. **Young patients are the highest-risk group.** Teens (26.1%) and young adults aged 19–30 (24.7%) miss the most. Risk falls steadily after 30, down to 14.9% for ages 61–75.
5. **Socio-economic and health signals.** Patients on a scholarship (Bolsa Família) miss 23.8%, against 19.9% for others. Patients with chronic conditions attend *better* (hypertension 17.3%, diabetes 18.0%), which fits with regular care building a habit.
6. **What barely matters:** gender (20.4% F vs 20.1% M) and weekday (19.5% to 21.3%). Neighbourhoods with 500+ appointments range from 15.7% (Do Cabral) to 29.1% (Santos Dumont).

## Recommendations

- **Send an SMS for every advance booking**, and add a second reminder 1–2 days before for bookings made 15+ days ahead.
- **Shorten lead times.** Keep more same-day or short-notice capacity, because no-shows concentrate in long waits.
- **Build a simple risk score** from lead time, prior no-show, age 13–30 and scholarship. Use it to overbook high-risk slots or phone those patients to confirm.
- **Follow up on repeat no-show patients** by flagging them at booking and confirming by phone.
- **Fix data capture.** Store Patient_ID as text, validate age, and block booking dates that fall after the appointment date.
