import React from "react";
import "./Style.css";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";

class FormMultiCheckbox extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      options: [],
      checked: []
    };
  }

  componentDidMount() {
    let checkedValues = [];
    if (this.props.defaultValue) {
      checkedValues = this.props.defaultValue.split('-');
    }
    this.setState({
      checked: checkedValues
    });
  }

  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  onCheckChanged = (option, checked) => {
    this.setState(prevState => {
      var newChecked = prevState.checked.filter(c => c != option.value);
      if (checked) {
        newChecked.push(option.value);
      }
      newChecked = newChecked.sort();
      return {
        checked: newChecked
      };
    }, () => {
      if (this.props.onChange) {
        this.props.onChange(this.state.checked.join('-'));
      }
    });
  }

  renderFormCheckbox = (option) => {
    return (
      <div class="custom-control custom-checkbox">
        <input
          id={"checkbox_" + option.value}
          className={
            this.shouldDisplayError()
              ? "custom-control-input is-invalid"
              : "custom-control-input"
          }
          type="checkbox"
          checked={this.state.checked.includes(option.value)}
          onChange={e => {
            this.onCheckChanged(option, e.target.checked);
          }}
          ref={input => {
            this.nameInput = input;
          }}
        />
        <label class="custom-control-label" for={"checkbox_" + option.value}>{option.label}</label>
      </div>
    );
  }

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.Id + "-group"}
          errorText={this.props.errorText}
          tabIndex={this.props.tabIndex}
          autoFocus={this.props.autoFocus}
        >
          <div className="rowC">
            <label htmlFor={this.props.id}>{this.props.label}</label>
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : (
                <div />
              )}
          </div>
          <div className="form-inline">
            {this.props.options.map((option) => this.renderFormCheckbox(option))}
          </div>
        </FormGroup>
      </div>
    );
  }
}
export default FormMultiCheckbox;
