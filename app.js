const {By, Builder, Key, until} = require('selenium-webdriver');
const fs = require('fs');
const Chrome = require('selenium-webdriver/chrome');
const lists = new Map([
    // ['psTravel', 'https://goo.gl/maps/GKpZNwjX1T1CtEsJA'], 
    // ['psWtg', 'https://goo.gl/maps/ShQb6ueDWqVEB6CD8'],
    // ['psShopping', 'https://goo.gl/maps/FxXUYLeuezncRVra9'],
    // ['psNOLA','https://goo.gl/maps/UryS3G16xyuRS4BH6'],
    // ['phTravel','https://goo.gl/maps/sCX3bsJi6nTHRBfs6'],
    // ['ihSEA','https://goo.gl/maps/ZbReXySdzft9B5Cy7'],
    // ['ihBerlin','https://goo.gl/maps/QjXvo2KFejLXL39Y7'],
    // ['phSEA','https://goo.gl/maps/otkdfPyyGE61oTzD9'],
    // ['harTravel','https://goo.gl/maps/3C6jRQPfE7BVJ9GB7'],
    // ['harShopping','https://goo.gl/maps/kVnPDH9ZnGCwTAn4A'],
    // ['zphWtg','https://goo.gl/maps/oJsTwqK8cY8rwGDi8'],
    ['psLong' , 'https://goo.gl/maps/XhsRmCDyz43E7qmz6'],

])
const destination = ''
const path = './output.json';

class Scraper {
    listUrl = ''
    title = ''
    headless = false
    length = 0
    timing = {
        'sleep':10,
        'keyRepeat':0
    }
    css = {
        'title':'h1',
        'subtitle':'h2.vkU5O',
        'scrollBox':'.m6QErb.DxyBCb.kA9KIf.dS8AEf',
        'item':'.WHf7fb',
        'itemFallback':'.OKhRId.afJXB',
        'content':'.IMSio',
        'backButton':'button.hYBOP.FeXq4d',  
        'loadingSpinner':'.qjESne'
    }
    regex = {
        'item': new RegExp('maps\/place'),
        'list': new RegExp('maps\/@')
    }
    constructor(listUrl, headless, css=this.css, regex=this.regex, timing=this.timing){
        this.listUrl = listUrl
        this.headless = headless
        return (async () => {
            this.driver = await this.getDriver();
            return this;
        })();
    }
    async execute() {
        const result = await this.scrape()
        await this.finish(result)
        return result
    }
    async scrape() {
        const title = await this.loadList()
        const content = await this.loopPlaces()
        const result = {
            'name':title,
            'items':content
        }
        return result
    }
    async finish(result){
        let payload = result
        if (payload.items.length) {
            await this.export(payload)
            await this.driver.quit()
        } else {
            console.log('Failed to scrape any places; retrying...')
            payload = await this.scrape()
            await this.finish(payload)
        }
    }
    async impatientClick(regex, css, i=0){
        let element =  (await this.driver.findElements(By.css(css)))[i]
        let url = await this.driver.getCurrentUrl() 
        while (url.search(regex)==-1) { 
            try {
                await element.click() 
                url = await this.driver.getCurrentUrl() 
            } catch (e) {
                if (e.name == 'ElementNotInteractableError') {
                    await new Promise(r => setTimeout(r, this.timing.sleep)) 
                    url = await this.driver.getCurrentUrl() 
                }
                else if (e.name == 'StaleElementReferenceError') {
                    element =  (await this.driver.findElements(By.css(css)))[i]
                }
                else console.log(e);    
            } 
        }
        return url
    }
    async getDriver() {
        const options = new Chrome.Options();
        this.headless == true && options.addArguments('--headless=new')
        const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();
        console.log("Driver initialized!")
        return driver
    }

    async loadList() {
        await this.driver.get(this.listUrl)
        this.listUrl = await this.driver.getCurrentUrl() 
        console.log("Going to Maps")
        const h1 = await this.driver.wait(until.elementLocated(By.css(this.css.title)),10000);
        const h2 = await this.driver.wait(until.elementLocated(By.css(this.css.subtitle)),10000);
        this.title = await h1.getText();
        const regexSub = /(?<number>\d+) places/i
        const subtitle = await h2.getText();
        const numPlaces = parseInt(subtitle.match(regexSub).groups.number)
        console.log(`Getting ${numPlaces} items from "${this.title}"`)
        const scrollbox = await this.driver.findElement(By.css(this.css.scrollBox))
        let items = await this.driver.findElements(By.css(this.css.item))
        let itemsLoaded = items.length
        if (!itemsLoaded) {
            this.css.item = this.css.itemFallback
            items = await this.driver.findElements(By.css(this.css.item))            
        }
        const regexSpinner = new RegExp(`[^.]${this.css.loadingSpinner.slice(1)}`, "g")
        let source = await this.driver.getPageSource()
        console.log("Preloading...")
        while (source.search(regexSpinner)!=-1) {
            if (items.length == itemsLoaded){
                await scrollbox.sendKeys(Key.PAGE_DOWN)
                itemsLoaded = items.length 
                items = await this.driver.findElements(By.css(this.css.item)) 
                await new Promise(r => setTimeout(r, this.timing.keyRepeat))
            }
            itemsLoaded = items.length 
            console.log(`Preloaded ${items.length} of ${numPlaces} places`)
            await new Promise(r => setTimeout(r, this.timing.sleep))
            source = await this.driver.getPageSource()
        }
        this.length = items.length
        return 
    }


    async loopPlaces() {
        console.log("Scraping places...");
        let result = []
        for (let i = 0 ; i < this.length ; i++) {
            const itemUrl = await this.impatientClick(this.regex.item,this.css.item, i)
            const splits = itemUrl.split('/')
            const name = decodeURIComponent(splits[5].replace(/(\+)/g,' '))
            const [lat,lon] = splits[6].replace(/(@)/g,'').split(',',2)
            console.log(`${name} (${lat}, ${lon}) | [${i+1}/${this.length}]`);
            result.push({"name":name, "coords":[lat, lon], "url":itemUrl})      
            await this.impatientClick(this.regex.list,this.css.backButton, 0)
        }
        return result
    }
    
    async export(content){
        const arr = []
        if (fs.existsSync(path)) {
            const existingData = JSON.parse(fs.readFileSync(path))
            arr.push(...existingData)
            }    
        content.size = content.items.length
        content.createdAt = new Date().toISOString();
        content.url = this.listUrl;
        arr.push(content)
        const newData = JSON.stringify(arr)
        await fs.writeFile(path, newData, (error) => {
            if (error) throw error
            console.log(`Successfully exported ${content.items.length} places to ${path}`)
        })
        return
    }
    async import(){
        

    }
}

const runAll = async ()=> {
    for (const [key,val] of lists){
        const instance = await new Scraper(val, false)
        await instance.execute()
    }
    return
}

runAll()
// incomplete load css:
// item container= .m6QErb 
// inner container = .OKhRId.afJXB
// button = .Opvxpd.TNluec
// thumb = .vy4oJ.yQlwUd
// h1 = fontHeadlineSmall edMet
// h1 = p0L2e fontBodyMedium
// image = img.BUmMSb


// normal list:
// item container= .m6QErb 
// inner padded div = .WHf7fb
// content container incl thumb = .IMSio
// content container excl thumb = .l1KL8d
// loading footer = .lXJj5c Hk4XGb
// loading spinner = .qjESne

// bug when list spans too big of a map area: map doens't load completely and the thing gets stuck.
