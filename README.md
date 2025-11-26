# Test Capacity Analytics App

Microservice and web UI to calculate test capacity and cycle times for production test stations.

## Stack

- Backend: FastAPI (Python), MongoDB (motor), JWT auth
- Frontend: React + Vite + Tailwind CSS
- Database: MongoDB
- Containers: Docker + docker-compose
- Hot reload:
  - Backend: `uvicorn --reload` with source mounted as volume
  - Frontend: Vite dev server with HMR and `src` mounted as volume

## Running the app

```bash
docker-compose up --build
```

Backend will be available at: http://localhost:8000  
Frontend will be available at: http://localhost:5173  

## Initial setup

1. Start the stack:

   ```bash
   docker-compose up --build
   ```

2. Create the initial admin user (only once).  
   Use Postman or curl:

   ```bash
   curl -X POST http://localhost:8000/api/auth/register-initial-admin \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "password": "changeme",
       "is_admin": true,
       "is_active": true
     }'
   ```

3. Login to get an access token:

   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=changeme"
   ```

   Copy the `access_token` returned in the response.

4. In your browser DevTools, set:

   ```js
   localStorage.setItem("access_token", "PASTE_TOKEN_HERE");
   ```

5. Reload http://localhost:5173  
   - Go to **Families** to register test families and their cycle time (in hours).
   - Go to **Analytics** to compute:
     - bottleneck type (equipment vs manpower)
     - input cycle time per unit
     - first unit arrival datetime
     - total duration to process all units
   - Go to **Users** to see the user list and activate inactive users (button "Give access").

## Data model (high level)

- **Users**
  - `username`, `email`, `password_hash`
  - `is_admin`, `is_active`

- **Families**
  - `name`
  - `test_cycle_time_hours`
  - `created_by_user_id`
  - `created_at`

- **analytic_test_cycle_time**
  - Inputs:
    - `family_id`
    - `sku`
    - `quantity`
    - `capacity_slots`
    - `manpower_qty`
    - `units_per_manpower_per_day`
    - `fecha_release` (target datetime for last unit to leave test)
  - Calculated fields:
    - `test_cycle_time_hours`
    - `bottleneck_type` (equipment / manpower)
    - `equipment_capacity_units_per_day`
    - `manpower_capacity_units_per_day`
    - `throughput_units_per_hour`
    - `input_cycle_time_hours`
    - `input_cycle_time_minutes`
    - `total_duration_hours`
    - `first_unit_datetime`
    - `is_feasible`
    - `created_by_user_id`
    - `created_at`

All business logic is in the `/api/analytics` POST endpoint.