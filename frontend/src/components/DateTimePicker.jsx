import React from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

function DateTimePicker({ value, onChange }) {
  return (
    <div className="w-full">
      <DatePicker
        selected={value}
        onChange={onChange}
        showTimeSelect
        timeIntervals={15}
        dateFormat="MM/dd/yyyy hh:mm aa"
        placeholderText="Select date & time"
        className="w-full rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-50"
        popperClassName="z-50"
      />
    </div>
  );
}

export default DateTimePicker;
