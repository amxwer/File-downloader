Download file by url
--------------------

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/amxwer/file_downloader.git
   cd file_downloader

Create a virtual environment:

python -m venv .venv
Activate the virtual environment:

On Windows:
.venv\Scripts\activate

2. Install the dependencies:

pip install -r requirements.txt

3.Set up environment variables.
Create .env file

4.Run migrations:

alembic upgrade head

## Usage

After starting the application, you can access it at `http://localhost:9999`. Use the following endpoints:

- **GET /file/{file_id}**: Retrieve information about a file by its ID.
- **POST /file/download**: Start a new file download task.
