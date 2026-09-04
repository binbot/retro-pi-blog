# Deployment Guide: Hosting Your Website on an Old Raspberry Pi

This guide outlines how to set up, secure, and deploy the retro-minimal website onto an older Raspberry Pi (e.g., Pi 1, Model B, Zero, Zero W) using **Raspberry Pi OS Lite** and **Nginx**.

---

## 1. Prepare the Raspberry Pi

To save as much RAM and CPU as possible, use a headless OS (no desktop environment).

1. Download the **Raspberry Pi Imager** from the official website.
2. Select **Raspberry Pi OS Lite (32-bit)** (this does not include a GUI and is highly optimized for older, low-memory boards).
3. Set your username, password, and Wi-Fi credentials in the Imager's customization options, and **enable SSH**.
4. Burn the OS to your SD card, insert it into the Pi, and boot it up.

---

## 2. Install Nginx Web Server

SSH into your Pi (e.g., `ssh username@raspberrypi.local` or its IP address) and run:

```bash
# Update package lists
sudo apt update

# Install Nginx
sudo apt install -y nginx

# Verify it is running
sudo systemctl status nginx
```

Nginx is extremely lightweight, typically using only 10–20MB of RAM, making it perfect for a 256MB or 512MB Pi.

---

## 3. Deploy the Website Files

1. Create the web root directory on your Pi:
   ```bash
   sudo mkdir -p /var/www/retro-blog
   sudo chown -R $USER:$USER /var/www/retro-blog
   ```

2. Copy the website files (all `.html`, `.css`, `.js` files, and folders like `posts/` and `media/`) to `/var/www/retro-blog`.
   You can use `scp` or `rsync` from your local machine:
   ```bash
   # Execute this command on your local development machine:
   rsync -avz /path/to/retro-pi-blog/ username@raspberrypi.local:/var/www/retro-blog/
   ```

3. Place your actual audio files in the `/var/www/retro-blog/media/` folder on the Pi (or add them via `./new-audio.sh`).

---

## 4. Configure Nginx

Create a custom configuration file for Nginx to serve the site.

1. Create a new site config file:
   ```bash
   sudo nano /etc/nginx/sites-available/retro-blog
   ```

2. Paste the following configuration (replace `yourdomain.com` with your actual domain or dynamic DNS name, or use `_` for default):

   ```nginx
   server {
       listen 80;
       listen [::]:80;

       server_name yourdomain.com www.yourdomain.com;

       root /var/www/retro-blog;
       index index.html;

       location / {
           try_files $uri $uri/ =404;
       }

       # Optimize caching for static assets
       location ~* \.(css|js|ico|gif|jpeg|jpg|png|svg|woff|woff2|ttf|eot)$ {
           expires 30d;
           add_header Cache-Control "public, no-transform";
       }

       # Optimize streaming for audio files
       location ~* \.(mp3|wav|ogg)$ {
           expires 7d;
           add_header Cache-Control "public, no-transform";
           add_header Accept-Ranges bytes; # Enables scrub bars to work smoothly
       }
   }
   ```

3. Enable the configuration and test it:
   ```bash
   # Enable the site
   sudo ln -s /etc/nginx/sites-available/retro-blog /etc/nginx/sites-enabled/

   # Remove the default Nginx welcome page
   sudo rm /etc/nginx/sites-enabled/default

   # Test config syntax
   sudo nginx -t

   # Reload Nginx
   sudo systemctl reload nginx
   ```

---

## 5. Security & Exposing to the Web (Port Forwarding & DDNS)

To allow visitors on the internet to see your site:

1. **Static IP**: Assign a static IP address to your Raspberry Pi in your home router settings.
2. **Port Forwarding**: In your home router, forward ports **80** (HTTP) and **443** (HTTPS) to your Raspberry Pi's local IP address.
3. **Dynamic DNS (DDNS)**: Since home IPs change, use a free DDNS service like [Duck DNS](https://www.duckdns.org/) or No-IP to get a free domain name (e.g., `myblog.duckdns.org`) that updates whenever your home IP changes.
4. **SSL (HTTPS)**: Encrypt your website with Let's Encrypt using `certbot`:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```
   *Certbot will automatically configure HTTPS redirect and handle SSL renewals.*

---

## 6. Extra Performance Optimization for Vintage Pi

Since your Pi has limited RAM and single-core CPU:

- **Disable Swap** (optional, prevents SD card wear and slow paging):
  ```bash
  sudo dphys-swapfile swapoff
  sudo dphys-swapfile uninstall
  sudo update-rc.d dphys-swapfile disable
  ```
- **Disable unused system services**:
  ```bash
  sudo systemctl disable bluetooth
  sudo systemctl disable avahi-daemon
  sudo systemctl disable triggerhappy
  ```
- Your idle RAM should now hover around **35MB**, leaving plenty of breathing room for handling incoming traffic!
