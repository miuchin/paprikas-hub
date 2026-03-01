// v4.3: force LIGHT theme for readability (disable dark mode)
  try{
    document.documentElement.classList.remove('dark');
    document.body && document.body.classList.remove('dark');
    localStorage.setItem('paprikasHubThemeV38DataFirst','light');
    localStorage.setItem('paprikasHubTheme','light');
  }catch(e){}