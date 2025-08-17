var config = {
    mode: "fixed_servers",
    rules: {
      singleProxy: {
        scheme: "http",
        host: "42.112.150.3",
        port: parseInt("13502")
      }
    }
  };
  
  chrome.proxy.settings.set({ value: config, scope: "regular" }, function() {});
  
  function callbackFn(details) {
    return {
      authCredentials: {
        username: "muaproxy689ef8202bc87",
        password: "lyl1nqbxq4ghgpyu"
      }
    };
  }
  
  chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    { urls: ["<all_urls>"] },
    ['blocking']
  );