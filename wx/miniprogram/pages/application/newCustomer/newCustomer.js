// pages/application/newCustomer/newCustomer.js
Page({

  /**
   * 页面的初始数据
   */
  data: {
    tindex:null,
    rindex:null,
    type: [],
    range: []
  },
  typeChange(e) {
    console.log(e);
    this.setData({
      tindex: e.detail.value
    })
  },
  rangeChange(e) {
    console.log(e);
    this.setData({
      rindex: e.detail.value
    })
  },
  addsuccess(e) {
    wx.showToast({
      title: 'add success',
    })
  },
  addfail(e) {
    wx.showToast({
      title: 'add fail',
    })
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage: function() {

  }
})