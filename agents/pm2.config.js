module.exports = {
  apps: [
    {
      name: 'agent-david',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'ceo', AGENT_NAME: 'David' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-david.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-amber',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'business_manager', AGENT_NAME: 'Amber' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-amber.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-robert',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'draftsman', AGENT_NAME: 'Robert' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-robert.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-tony',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'labor_coord', AGENT_NAME: 'Tony' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-tony.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-john',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'land_broker', AGENT_NAME: 'John' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-john.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-mark',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'realtor', AGENT_NAME: 'Mark' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-mark.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-aryan',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'accountant', AGENT_NAME: 'Aryan' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-aryan.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-antonio',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'qc_manager', AGENT_NAME: 'Antonio' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-antonio.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-syed',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'software_engineer', AGENT_NAME: 'Syed' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-syed.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    },
    {
      name: 'agent-pipeline',
      script: './agent_wrapper.py',
      cwd: '/Users/davidschy/geniinow-projects/agents',
      env: { AGENT_ROLE: 'pipeline', AGENT_NAME: 'Pipeline' },
      log_file: '/Users/davidschy/geniinow-projects/logs/agent-pipeline.log',
      autorestart: true,
      max_restarts: 5,
      min_uptime: '10s'
    }
  ]
};
