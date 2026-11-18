-- Starter data. Change the admin email to your own Google account BEFORE running.
insert into public.admin_emails(email) values ('clayxculture@gmail.com') on conflict do nothing;
insert into public.store_settings(key,value) values
('brand','"calyxculture"'),('whatsapp','"918899190631"'),('phone','"+91 8899190631"'),
('address','"Housing Colony, Jamia Market, Near Jamia Ahli-Hadees, Bemina, Srinagar, Jammu & Kashmir, India"'),
('instagram','"https://www.instagram.com/calyxculture_/"'),('announcement','"New season styles are in. Order on WhatsApp"'),
('free_ship_threshold','1999'),('shipping_fee','99'),('sizes','["S","M","L","XL"]'),
('delivery','{"dispatch_days":1,"skip_sunday":true,"valley":[1,3],"jk":[2,4],"india":[4,7]}'),('risk_review','30'),('risk_reject','60'),('cod_cap_first','2500'),('policy_version','"2026-11-14.1"')
on conflict (key) do nothing;
insert into public.faq(question,answer,keywords,sort) values
('Is Cash on Delivery available?','Yes. You can pay Cash on Delivery, or send your order on WhatsApp and pay when it arrives.','cod,cash,pay on delivery,payment,pay',1),
('How long does delivery take?','Our team confirms the delivery time and shipping charge for your pincode on WhatsApp. Shipping is free once your bag crosses the free-shipping amount shown in the bag.','delivery,shipping,ship,deliver,days,how long,charge,time',2),
('What is the return or exchange policy?','We do not accept returns. We exchange only verified defects, wrong items, transit damage or missing items reported within 3 days of delivery with an unboxing video. See the Policies page for details.','return,refund,exchange,replace,policy',3),
('Which size should I pick?','We stock S, M, L and XL. Most styles are relaxed or oversized. Send your height and weight on WhatsApp and we will recommend a size.','size,sizes,fit,sizing,measurement,chart',4),
('Where is your store?','Housing Colony, Jamia Market, Near Jamia Ahli-Hadees, Bemina, Srinagar, Jammu & Kashmir, India.','address,store,shop,location,visit,where are you',5),
('How can I contact you?','WhatsApp or call us on +91 88991 90631.','contact,phone,call,number,whatsapp,talk,help',6),
('Can I pay online with UPI or card?','Online payments are not live yet. For now you can pay Cash on Delivery, and online payment options are coming soon.','upi,card,online,razorpay,netbanking,gpay,phonepe',7),
('Where can I follow you?','Follow us on Instagram at instagram.com/calyxculture_.','instagram,insta,social,follow',8),
('What is calyxculture?','calyxculture is a modern streetwear brand from Srinagar, Kashmir, making stylish, comfortable, quality clothing.','about,brand,who are you,calyx,calyxculture,story',9);
