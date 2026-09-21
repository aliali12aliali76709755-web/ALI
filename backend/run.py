import os
import uvicorn

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f'Starting Uvicorn server on port {port}...')
    uvicorn.run('server:app', host='0.0.0.0', port=port, log_level='info')
