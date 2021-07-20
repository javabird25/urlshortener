# urlshortener

## Deployment
1. Create `db-password.txt` with a random password in the repository root.
2. Run `docker-compose up`.
3. On first start, run `docker-compose exec backend python manage.py migrate`.
