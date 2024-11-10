 Create directory structure
mkdir -p data/databases

# Set permissions
chmod -R 777 data

# Initialize databases
python setup_databases.py

# Set database file permissions
chmod 666 data/databases/*.db

echo "Local setup completed!"