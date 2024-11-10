# Steps to setup environment and run Python code
1. Install Python 3
   ```brew install python3```
2. Create virtual environment (if not already created)
  ```python3 -m venv venv```
3. Activate virtual environment
  ```source venv/bin/activate```
4. Verify you're in venv (should show venv path)
  ```which python```
5. Install requirements
  ```pip install -r requirements.txt```
6.  Run Python code
  ```python main.py```
7. Run tests 
  ```python -m unittest test.py```  
8. To deactivate when done
  ```deactivate```