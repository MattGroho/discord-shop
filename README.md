# Discord Shop Bot
![Server Logo](https://i.imgur.com/EghS9yh.png)

Thank you for viewing the official documentation for the Discord shop bot. In this document we’ll cover all the commands necessary to add, delete, and modify items in your shop.

Please note all commands are shallowly covered on our server by using the *help command. Affiliates are also able to use *help Command for additional info on a given command.

## Setting up your first item
The first command you’ll need to get familiar with is add_item. With this command, you’ll be able to add additional items to your shop. The arguments for the command can be found below:

`*add_item Name Price Quantity Type Image Description`

Name: Must be surrounded with quotation marks to achieve spaces in your item name.
	Eg. “Test Item”
Price: Any normal price in USD.
	Eg. 1.00
Quantity: The available quantity for your item, a negative quantity will make it appear infinitely available for customers.
	Eg. 20 or -1
Type: The type of the item.
	Eg. digital, service or method
Image: The image you want to display for your item. This must be a direct url to an image featuring .png or .jpg behind the url. We recommend using Imgur or Discord to upload images and copying the url from that image. You can also type in none for the url to use no image. The url must be less than 128 characters long.
	Eg. https://i.imgur.com/1sgUyPn.png or none
Description: The description for your item. Again, since this will most likely contain multiple words you must surround the description with quotation marks. The description must be less than 256 characters long.
	Eg. “A test description for my item”

With these arguments down, we can assemble our item and add it to our shop by substituting it into the add_item command.
	Eg. `*add_item “Test item” 1.00 -1 none “A test description for my item”`

## Item modification commands
After adding items to your shop, you may want to edit the item without having to re-add it to the shop. Luckily, this is where our item modification commands come into help! All formatting stays the same between adding an item and the edit commands such as quotations around spaced words and character limits. 
Before you can modify an item, it’s crucial that you enable Developer Mode on Discord for the ability to copy your item message id for editing. To do this, navigate to User Settings -> Appearance -> Developer Mode and be sure this is active.

After enabling Developer Mode, you’re able to right click to the right of your shop items (not inside the embed of the item) and click Copy ID to obtain your item ID for the following commands.

### Below are several commands to help you edit existing items in the shop:

`*set_item_name ID Name`

* ID: The message ID of your shop item.
* Name: The new name of the item (surrounded with quotations for multiple words)

`*set_item_price ID Price`

* ID: The message ID of your shop item
* Price: The new price of the item

`*set_item_quantity ID Quantity`

* ID: The message ID of your shop item
* Quantity: The new quantity of the item (negative for INF item listing)

`*set_item_type ID Type`

* ID: The message ID of your shop item
* Type: The new type of the item (digital, service, or method)

`*set_item_image ID Image`

* ID: The message ID of your shop item
* Image: Thew new image for the item (direct url or none)

`*set_item_desc ID Description`

* ID: The message ID of your shop item
* Description: The new description of your item (surrounded with quotations for multiple words)

### Deleting an item from your shop
After creating an item, you might want to delete it from your shop. In order to do this, the following command will let you delete those items:

`*delete_item ID`

* ID: The message ID of your shop item

### Opening and Closing your shop to the public
After you have your shop configured to your likeness, you can open it to the server for others to view. The lock icon in the upper-righthand corner of the shop channel hashtag indicates whether the channel is currently publicly viewable. Below demonstrates the command for this:

`*shop Status`

* Status: The status for your shop to be publicly visible. Either open or close

### Modifying aspects of the shop
Once the shop has been set up you may find yourself wanting to edit the description of your shop in case you have a dedicated shop to link your customers to or would like to specify payment details or contact information. Below demonstrates the command(s) to modify the shop.

`*set_shop_desc Description`

* Description: The new description for your shop (surrounded with quotations for multiple words)
