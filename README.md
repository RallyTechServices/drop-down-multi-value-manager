# drop-down-multi-value-manager
Tool to keep a drop-down multi-value field in Agile Central consistent with values in a text file.
If the values have a "key" portion of the value (e.g. "1234 My Value") then the app will update
any values that start with same string (e.g. "1234 My NEW Value").

Run first with `"preview": true` to see the changes that will occur. Preview mode does not make changes
in Agile Central.

## Usage
1. Setup Python and install dependencies (`pyral` is the only actual dependency which pulls in the others
from `requirements.txt`)
    * `pip install -r requirements.txt`
1. Setup environment variables
    * `RALLY_USER=user@company.com`
    * `APIKEY=_12345689...`
2. Edit `config/config.json` to set preview mode, the element name and attribute name.
3. Edit `config/desired_values.txt` to the values you want to use. One value per line
4. (optional) Edit `config/logging.json` to control logging output and location. Default is to a file
and the console.
5. `python ValueManager.py config/config.json config/desired_values.txt`